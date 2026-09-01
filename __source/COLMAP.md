---
title: Structure-from-Motion Revisited
aliases:
  - Schonberger 2016
  - Schönberger 2016
  - Structure-from-Motion Revisited
first_author: Johannes L. Schönberger
year: 2016
venue: CVPR
school:
  - University of North Carolina at Chapel Hill
  - ETH Zurich
kind: method
task:
  - SfM
  - camera pose
  - 3D reconstruction
code: https://github.com/colmap/colmap
status: read
pdf: "[[COLMAP.pdf]]"
tags:
  - paper
---
[[COLMAP.pdf]]

[[Structure from Motion]]문제를 해결하는 새로운 방식을 제시한다.

문제 상황: 기존 SfM 알고리즘들은 완전성과 robustness 측면에서 아쉬운 결과를 보임

![[Pasted image 20260810145954.png]]
## 4. Contributions
### Scene Graph Augmentation
1. [[Fundamental Matrix]] 추정
2. Homography 변환 생성
3. [[Essential Matrix]] 추정
4. 두 모델(Fundamental matrix, homography) 중 더 적절한 모델을 선택하기 위해 [[GRIC]]이라는 model selection methods를 근사한 방식을 사용

**Model selection methods**: Inliers의 수를 나타내는 $N_F, N_H, N_E$를 정의하고 센다. 이들의 비율과 $\epsilon_{HF}$의 비교를 통해 어떤 모델을 선택할지 결정한다. 

Internet에서 수집한 사진들을 데이터로 사용하기 때문에, watermarks, timestamps, and frames(WTFs)가 등장한다는 문제가 있다. 이를 다루기 위해 이미지 가장자리에 대해 similarity transformation을 추정한다. 이를 이용해 similarity transformation inlier의 수를 $N_S$라 정의하고, $N_F$와  $N_E$로 나눈다. 그 값이 각각 $\epsilon_{SF}, \epsilon_{EF}$보다 하나라도 크다면 WTF로 판단한다. 

### Next Best View Selection
이 문제는 이미 여러 3D 점들이 존재하는 상황에서, 다음에 어떤 이미지를 모델에 등록할지(incremental 방식)를 결정하는 문제다. PnP 방식으로 카메라의 pose를 추정할 때 랜덤한 순서로 이미지를 추가하면 에러가 계속 쌓이고 연쇄적으로 전파되기 때문에, *등록하기 좋은 이미지*를 알아내야 한다.

기존 방식: Bundler. 아직 등록되지 않은 이미지 중에서 모델이 이미 삼각측량한 3D점을 가장 많이 갖고 있는 이미지를 선택.

COLMAP에서 제시하는 방식: 그런 점들의 개수와 공간적 분포를 모두 고려하는 방식

$\mathcal{S}$를 정의해 해당 값(score)이 가장 높은 이미지를 next best view로 선택한다. 이 값은 visible points가 많을 수록, 그리고 uniform 할 수록 높아지도록 설계된다. 구체적인 방법은 아래와 같다.
1. 이미지를 격자로 쪼갬
2. 각 cell에 포함된 점이 reconstruction 과정에서 3D points에 대응된다면 cell의 상태를 empty에서 full로 바꿈
3. full로 상태를 바꿀 때마다 $\mathcal{S}_i$를 $w_l$만큼 증가시킴
문제점: Visible points의 수가 cell의 수보다 많이 작다면 points의 분포를 제대로 나타낼 수 없음
$\rightarrow$ Cell의 수를 증가시켜 가면서 반복하는 multi-resolution pyramid 방식을 사용([[SIFT]]에서 사용된 방법과 유사한 듯)

### Robust and Efficient Triangulation
우선 feature track이 뭔지 알아야 한다. Feature track $\mathcal{T}$는 같은 지점을 보고 있는 모든 이미지의 위치들의 집합이다. 보통은 많은 수의 outliers를 포함하게 된다. 서로 다른 3D points가 같은 track으로 잘못 합쳐지는 경우, 기존 방식인 Bundler는 이를 복구할 수 없다. 

따라서 이 논문에선 해당 과정을 [[RANSAC]] 방법으로 처리한다. 
1. $\mathcal{T}$에서 관측 2개를 랜덤 샘플링해 3D point 하나 추정
2. 해당 Point가 나머지 관측들에 대해 consensus한지 체크
3. 최대 consensus set을 주는 점을 채택
4. 남은 관측들에 대해 재귀적으로 반복

### Bundle Adjustment
새로운 이미지를 추가할 때마다 local BA를 수행하고, 모델이 일정 크기 이상으로 커졌을 때만 global BA를 수행한다. 

BA를 수행한 후 모델과 일치하지 않는 결과는 필터링 해야 한다. Triangulation angle이 최솟값 이상인지, 카메라의 intrinsic parameter가 물리적으로 말이 안 되는 값으로 수렴하지 않았는지(degenerate cameras) 확인한다. 

Re Triangulation 단계는 BA 이전 뿐만 아니라 이후에도(post-BA RT) 진행한다. 

### Redundant View Mining
SfM을 풀 때 가장 큰 병목은 BA이기 때문에, 겹치는 부분이 많은 이미지들을 cluster로 묶어서 BA 단계에서 마치 하나의 카메라처럼 파라미터화한다. 그룹 내부의 상대적인 위치는 고정시키고 cluster 단위로 이동시키며 최적화 시킨다.