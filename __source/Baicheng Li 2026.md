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
