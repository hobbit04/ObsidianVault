---
tags:
  - ComputerVision
  - 3D
---
여러 장의 2D 사진들을 이용해 3D 구조와 카메라들의 위치, 각도를 복원하는 문제를 *SfM* 이라고 부른다.

[[Epipolar Geometry]]와 유사하다고 볼 수 있으며 이를 이미지 2 장이 아닌 수백~수만 장으로 확장한 것이다.

이를 다루는 방식은 크게 세 가지가 있다([[Johannes L. Schonberger 2016|COLMAP]]).
1. **Incremental**: 가장 널리 사용되는 방식
2. Hierarchical
3. Global approaches
2016년의 논문 [[Johannes L. Schonberger 2016|COLMAP]]에서는 새로운 방식인 COLMAP을 제시했다. 

기본적으로 Incremental 방식의 SfM은 아래와 같은 단계를 거친다.
## Correspondence Search
**Feature Extraction**
각 이미지에 대해 $\mathcal{F}_i=\{(x_j, f_j)|j=1 ... N_{F_i}\}$ 를 구한다. 즉 위치와 피쳐를 구하는 것이다. 사용하는 피쳐로는 [[SIFT]], 그의 미분값 등이 있다. 

**Matching**
겹치는 scene이 있을 것으로 추정되는 set을 만드는 것을 목표로 한다. Naive한 접근으로는 두 이미지의 features를 모두 비교해 보는 방법이 있지만 매우 시간 복잡도가 크기 때문에 효율적인 접근들이 많이 연구되고 있다. 최종적으로 결과는 $\mathcal{C}=\{\{I_a, I_b\}|I_a, I_b \in \mathcal{I}, a < b\}$ 으로 나타난다. 이를 *potentially overlapping image pairs*라고 한다.

**Geometric Verification**
$\mathcal{C}$를 검증하는 단계이다. [[RANSAC]] 등의 방법을 이용할 수 있으며 이 단계의 최종 결과는 scene graph라고 하는, 이미지를 노드로 하고 같은 scene이 나타난 것으로 확인된 쌍을 엣지로 연결한 그래프가 된다. 
## Incremental Reconstruction
*이 단계에서 개선된 해결 방법을 제시한 논문이 [[Johannes L. Schonberger 2016]] 이다.* 

**Initialization**
Two-view reconstruction 방식을 이용할 때 적절한 초기 pair를 선택하는 것이 중요하다. 이미지 그래프에서 연결의 밀도가 높은 지점에서 시작하는 것이 보통 정확한 결과로 이어진다. 

**Image Registration**
3D 모델을 이미 Correspondence Search 단계에서 구해놨으므로, 여기에 새로운 이미지를 하나씩 추가하면 된다. 새로운 이미지 $I_{\text{new}}$의 features 중 일부가 이미 등록된 이미지와 매칭된다면 해당 feature가 대응되어 있던 3D point $X_k$에 이 점을 대응시킬 수 있다. 

이를 위해선 카메라의 pose를 구해야 하는데, 이를 Perspective-n-Point(PnP) 문제라고 한다. 이 문제는 [[RANSAC]]과 minimal pose solver 를 활용해 해결할 수 있다. 

**Triangulation**
한 물체를 두 가지 시점에서 바라보면, 각 시점의 위치에서 뻗어져 나온 ray 두 개를 이용해 물체의 3차원 위치를 추정할 수 있다. 이를 삼각측량(triangulation)이라고 한다.

**Bundle Adjustment**
위의 과정들만으로는 카메라 pose의 불확실성이 삼각측량 된 점의 불확실성을 높이고, 이 불확실성의 전파가 계속 반복된다. 따라서 refinement 과정이 필요하다. BA 과정에서는 reprojection error를 아래와 같이 정의한 후 최소화 시킨다. $$E=\sum_j \rho_j(||\pi(P_c, X_k)-x_j||^2_2)$$이때 $\pi$는 scene points를 image space 로 전사하는 함수이다. $\rho$는 [[Robust loss function]] 이다. 이 최적화 문제를 풀기 위해서 *Levenberg-Marquardt* 방법을 사용한다. 