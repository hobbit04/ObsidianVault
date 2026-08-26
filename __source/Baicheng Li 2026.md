---
Title: |-
  MV-SAM3D: Adaptive Multi-View Fusion for
  Layout-Aware 3D Generation
School:
  - Peking University
---
[[MV-SAM3D.pdf]]

SAM3D: 하나의 이미지와 segmentation masks를 이용해 각 object의 3d 구조와 텍스쳐를 layout-aware 하게 만들어냄

두 가지 문제점;
1. Multi-View Consistency
2. Physical Plausibility in Multi-Object Scenes
위 문제점들을 해결하기 위해 SAM3D를 확장한 논문이다.

## Related work
- [[Jianfeng Xiang 2025]]

## Method
먼저 SAM3D에서 어떻게 처리했는지를 알아야 한다. 
### Sparse Structure Generation
Input: Image, Mask, Pointmap
- Mask는 crop용이 아니라 conditioning용. crop 뷰 + full-scene 뷰를 **둘 다** 넣어서 layout을 알 수 있게 함
- Pointmap은 MoGe(monocular depth)로 획득
Output: Shape(3D asset), Layout parameter($s, R, t$)
- 실제 출력은 sparse voxel structure $\mathcal{V} \in \mathbb{R}^{K_1 \times d_1}$ (coarse geometry)
- MM-DiT로 shape과 layout을 **동시에** 예측 (pose가 후처리가 아님)

### SLAT Generation
Input: Stage 1의 sparse structure + 이미지 conditioning feature
Output: Structured latent $Z \in \mathbb{R}^{K_2 \times d_2}$ → 고해상도 geometry + texture
- DiT 구조, latent token과 이미지 feature 간 **cross-attention** 사용

두 stage 모두 flow matching: $x_{t+\Delta t} = x_t + v_\theta(x_t, t, c)\cdot\Delta t$
object마다 이 파이프라인을 **독립적으로** 돌린다 → 문제점 2(물리적 타당성)의 원인

## Adaptive Multi-View Fusion
[[Multi Diffusion]] 프레임워크를 도입한다. 이때 총 $N$개의 multi view images가 있다면 각 viewpoints를 이용해 $N$개의 조건을 부여한다. 기본적인 Multi diffusion에서는 $N$개의 velocity를 단순하게 $1/N$을 곱해 사용했지만, 이 논문에서는 **Attention-Entropy Weighting**과 **Visibility Weighting**을 사용한다. 수식에서 $w_i$로 나타난 부분이다. $$\hat{v}(x_t,t)=\sum_{i=1}^Nw_i\cdot v_\theta (x_t,t,c_i)$$
왜 naive 하게 평균을 내면 안될까? 모든 시점이 동일한 퀄리티의 정보를 담고 있지 않기 때문이다. 가려졌거나, 흐릿하게 보이는 시점에서의 $v$가 제대로 object가 보이는 시점에서의 $v$와 동일하게 취급되면 결과물이 나빠질 수 있다.

### Attention-Entropy Weighting
Attention 패턴이 각 상황에서 어떻게 형성될지 생각해보자. 우선 latent space에서의 각 vector는 flow matching 과정에서 이미지 패치 토큰을 attend 한다. 이 cross-attention 과정을 수행하면 하나의 latent에 대한 각 패치의 중요도를 얻게될 것이다. 
만약 이미지 안에 latent에 해당하는, 혹은 관련이 깊은 패치가 존재한다면 해당 패치의 어텐션 값은 높게, 나머지 패치의 어텐션 값은 낮게 나올 것이다. 이는 낮은 엔트로피로 이어진다(어텐션 자체의 분포가 낮은 엔트로피를 갖음). 
반면 전혀 관련 없는 패치들만 있다면, 모두 균등하게 낮은 값이 나올 것이다. 이러면 높은 엔트로피가 계산될 것이다.
>만약 이미지 전체가 latent와 높은 연관성을 갖는다면? 엔트로피는 높게 나올텐데 중요한 view로 봐야할텐데?

엔트로피는 다음과 같이 정의 된다. $$H_i(l)=-\frac{1}{\log P}\sum_{p=1}^P\hat{a}_{i,l}^{(p)}\log \hat{a}_{i,l}^{(p)}$$이때 $i$는 view point, $P$는 이미지 패치 토큰, $\hat{a}_{i,l} \in \mathbb{R}^P$는 어텐션 가중치이다. 이 엔트로피를 이용해서 가중치는 다음과 같이 정의된다. 
$$w_i^{\text{ent}}(l)=\frac{\exp(-\alpha \cdot H_i(l))}{\sum_{j=1}^N\exp(-\alpha \cdot H_j(l))}$$
여기서 $\alpha$는 temperature parameter다. 

### Visibility Weighting
