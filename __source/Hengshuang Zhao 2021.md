---
Title: Point Transformer
School:
  - University of Oxford
  - The University of Hong Kong
  - The University of Hong Kong
Lab:
  - Intel Labs
Conference: CVPR
---
[[Point Transformer.pdf]]

기여: 3D point clouds를 위한 트랜스포머 아키텍쳐를 제시했다.
문제: Semantic scene segmentation, Object part segmentation, Object classification 등 3D point clouds processing

## Point Transformer
[[Vector Attention]]을 사용해 [[Point Cloud]]를 처리한다. Point cloud는 근본적으로 집합이기 때문에, 순서가 상관없는 self-attention과 궁합이 좋다.

> 개념 자체(scalar attention과의 차이, softmax 방향, output의 의미)는 [[Vector Attention]] 참고. 여기서는 이 논문이 그것을 어떻게 변형해 썼는지만 다룬다.

### Point Transformer layer
Vector attention의 일반형(Eq. 2)을 point cloud에 맞게 고친 것이 Eq. 3이다.$$y_i=\sum_{x_j\in \chi(i)}\rho(\gamma(\varphi(x_i)-\psi(x_j)+\delta))\odot (\alpha(x_j)+\delta)$$일반형에서 바뀐 지점은 두 가지다.

1. **$\mathcal{X} \to \chi(i)$** — 전체 점이 아니라 $i$번째 점의 **kNN 이웃**으로 제한한다. 점이 수만 개라 전역 어텐션은 계산량이 감당되지 않는다. 즉 local attention.
2. **$\alpha(x_j) \to \alpha(x_j)+\delta$** — position encoding을 value에도 더한다. $\delta$가 어텐션 가중치 계산용과 value 보정용으로 **두 번, 서로 다른 역할로** 등장하는 셈이다. Ablation상 둘 다 넣는 쪽이 가장 좋았다.

여기서 $\delta=\theta(p_i-p_j)$이고 $\theta$는 MLP다. 즉 위치 $p$가 관여하는 통로는 **① kNN으로 이웃을 고를 때 ② $\delta$를 계산할 때** 두 곳뿐이다.

다이어그램으로 나타내면 아래와 같다. ![[Pasted image 20260823205854.png]]

이 layer는 단독으로 쓰이지 않고 residual block 안에 들어간다.$$x \to \text{linear} \to \text{PT layer} \to \text{linear} \to (+\,x)$$따라서 $y_i$는 블록의 최종 출력이 아니라 residual branch의 출력이다.
