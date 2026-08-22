---
tags:
  - 3D
  - ComputerVision
---
Paper: [[Bernhard Kerbl 2023]]
Demo: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/

줄여서 3DGS 라고도 하는 이 기법은, 3D scene을 약 수백만 개의 수많은 3D 가우시안들의 합으로 기술하는 방법이다. 신경망을 사용하지 않는, explicit 한 3d representation 방법이다. 
## Scene 표현 방법
하나의 가우시안은, 다음과 같은 파라미터를 가진다.

| 파라미터                                | 의미                              |
| ----------------------------------- | ------------------------------- |
| $\mu \in \mathbb{R}^3$              | 중심 위치                           |
| $\Sigma \in \mathbb{R}^{3\times 3}$ | 모양/방향 cf) [[Covariance Matrix]] |
| $\alpha$                            | 불투명도                            |
| SH계수                                | View-dependent 색상               |
위 네 개의 파라미터로 정의되는 가우시안 $G(x)$는 다음과 같다. $$G(x)=\exp(-\frac{1}{2}(x-\mu)^T\Sigma^{-1}(x-\mu))$$

## Rendering 방법
## 학습 방법