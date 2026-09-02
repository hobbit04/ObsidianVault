---
title: "MV-SAM3D: Adaptive Multi-View Fusion for Layout-Aware 3D Generation"
school:
  - Peking University
tags:
  - paper
---
[[MV-SAM3D.pdf]]

SAM3D: 하나의 이미지와 segmentation masks를 이용해 각 object의 3d 구조와 텍스쳐를 layout-aware 하게 만들어냄

두 가지 문제점;
1. Multi-View Consistency
2. Physical Plausibility in Multi-Object Scenes
위 문제점들을 해결하기 위해 SAM3D를 확장한 논문이다.

## Related work
- [[TRELLIS]]

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
위의 attention-entropy는 결국 모델이 implicit하게 연관성을 배우는 것이라 비슷하지만 다른 위치에 있는 물체가 view에 포함되는 경우 등의 상황에선 오작동할 수 있다. 
Explicit한 가중치가 필요한 이유고, 이는 Sparse Structure Generation 단계에서 생성된 [[Voxel]]구조 $\mathcal{V}$를 이용한다. [[DDA ray tracing]]기법을 사용해 $V\in\{0, 1\}^{N\times K}$ 를 생성한다. 이때 $V_{i,l}=1$이라는 것은 $i$번째 view point에서 $l$ latent가 보인다는 뜻이다. 이를 이용해서 가중치는 다음과 같이 정의된다. $$w_i^{\text{vis}}(l)=\frac{\exp(\beta \cdot V_{i,l})}{\sum_{j=1}^N\exp(\beta\cdot V_{j,l})}$$여기서 $\beta$는 occlusion을 얼마나 패널티 줄지를 결정하는 값이다. 

최종적으로는 두 가중치를 $\gamma$ 비율로 섞어서 사용한다.

## Physics-Aware Pose Estimation
Adaptive multi-view fusion 과정에서 각 object 별로 pose를 추정할 수는 있지만, 합쳐놓고 보면 서로 겹치거나 공중에 떠 있는 등 물리적으로 불가능한 scene이 나오는 경우가 많다. 이를 해결하기 위해 도입한 두 가지 방법을 소개한다.

### Layout Injection
Flow matching 과정 후반부터 주기적으로 디코더를 돌려 voxel occupancy를 얻는다. 이를 이용해 $\mathcal{L}_{\text{collision}}, \mathcal{L}_{\text{contact}}$ 를 계산하고 둘의 가중합으로 정의된 $\mathcal{L}_{\text{phys}}$를 얻는다. 이후 flow matching 과정에 gradient 항으로써 추가한다. $$x_t+\Delta t=x_t + v_\theta(x_t,t,c) \cdot \Delta t-\eta \nabla_{x_t} \mathcal{L}_\text{phys}$$논문에 정확한 collision, contact loss 수식은 나와 있지 않다.

### Post-Generation Pose Refinement
위의 과정은 생성(flow matching) 중간에 일어나는 일이었고, 이 과정은 모든 object가 생성된 후에 진행하는 교정 과정이다. Output [[Mesh]]에 대해서 global pose refinement를 수행한다. 이때 각 오브젝트마다 similarity transform $\theta_k(s_k,R_k,t_k)$를 정의하고 이를 최적화한다. 
$$\mathcal{L}_{\text{total}} = \sum_k \mathcal{L}_{\text{align}}^{(k)} + \lambda_{\text{col}} \sum_{j \neq k} \mathcal{L}_{\text{col}}^{(j,k)} + \lambda_{\text{con}} \sum_{j \neq k} \mathcal{L}_{\text{con}}^{(j,k)} + \lambda_{\text{reg}} \mathcal{L}_{\text{reg}}$$
역시, 각 loss에 대한 수식은 나와 있지 않다. 
## Experiments
