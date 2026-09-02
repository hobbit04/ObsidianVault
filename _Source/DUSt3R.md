---
title: "DUSt3R: Geometric 3D Vision Made Easy"
venue: CVPR
school:
  - Aalto University
lab:
  - Naver Labs Europe
tags:
  - paper
---
[[DUSt3r.pdf]]

이 논문에선 [[Multi View Stereo Reconstruction|MVS]] 문제를 푸는 새로운 방식을 제안한다. [[Structure from Motion]] 문제가 카메라의 정보를 결과로 내놓으면 이를 이용해 MVS를 해결하는 식으로 파이프라인이 되어 있었는데, 여기선 SfM과 MVS를 하나의 forward pass로 통합해 해결하는 end-to-end 방법을 제안한다. 

DUSt3r은 *Dense and Unconstrained Stereo 3D Reconstruction*의 약자다. 

이 방법을 이용하면 바로 3D depth 정보를 알아낼 수 있을뿐만 아니라 이를 이용해 역으로 pixel matches와 cameras 정보(SfM을 해결해야 알 수 있던 정보들)를 구할 수도 있다.

## Method
### Pointmap
논문에서 $X \in \mathbb{R}^{W\times H\times 3}$로 표기되는 pointmap은, 3D 점들에 대한 dense 2D field이다. 2D image의 각 픽셀에 대해 3차원 벡터가 대응되어 픽셀과 3D point의 대응을 나타낸다. 

### Overview
목표: $\mathcal{F}$ 학습
Input: $I^1, I^2$. 2 RGB images
Output: $X^{1,1}, X^{2,1}$. 2 corresponding pointmaps, and $C^{1,1},C^{2,1}$. 2 confidence maps
좌표의 표현 기준은 항상 첫번째 이미지, $I^1$이다. 두 이미지의 크기가 다를 수도 있지만, 설명할 때는 같다고 가정한다.
![[Pasted image 20260811124552.png]]
CroCo에서 영감을 받은 네트워크 디자인이라고 한다.

두 개의 입력 이미지가 같은 ViT 인코더를 통과해 $F^1, F^2$를 만들어낸다. 이 둘은 각각 다른 Transformer 디코더에서 순차적으로 self-attention과 cross-attention, 마지막으로 MLP layer를 통과한다. Cross-attention은 매 디코더 블록마다 수행되며 디코딩 과정에서 서로 정보를 교환하게 한다. 최종 결과인 $X, C$를 만들 때 사용되는 regression head는 각 디코더 블록의 결과를 모두 사용한다. 이런 구조를 DPT head, [[Dense Prediction Transformer]] head 구조라고 한다.

### 3D Regression loss
모델이 내놓은 3차원 pointmap과 실제 ground truth pointmap을 이용해 손실함수를 정의해야 한다. 이 regression loss는 두 pointmap의 각 위치의 차이, 즉 유클리드 거리로 정의된다. 그 전에 normalize도 수행한다. 하나의 이미지로는 실제 스케일을 알 수 있는 방법이 없기 때문이다.
### Confidence-aware loss
이미지의 어떤 부분은 유독 예측하기 어려울 수 있으므로 confidence를 추가해 새로운 손실함수를 정의한다. 위의 regression loss를 $l_{\text{regr}}$이라 할 때 최종 손실함수는 $$\mathcal{L}_\text{conf}=\sum_{v\in\{1, 2\}}\sum_{i\in\mathcal{D}^v}C_i^{v, 1}l_\text{regr}(v,i)-\alpha \log C_i^{v, 1}$$로 정의할 수 있다. 자신감이 높을 수록 $l_\text{regr}$이 작아야 하고, 자신이 없는 부분에 대한 loss 는 약간 봐주는 것으로 이해할 수 있다. 첫 번째 항만 존재하면 모델은 $C$를 0으로 만드려 할 것이므로 정규화 항이 필요하다. 이때 $C$가 1보다 크도록 수식을 정의해 confidence가 커지면 무조건 손실을 낮추는(음의 방향으로 잡아당기는) 효과가 있도록 한다. 따라서 두 번째 항은 모델이 confidence를 최대한 키우고 싶도록 설계된 것으로 볼 수 있다. 이러면 하늘이나 가려진 영역처럼 정답을 맞추기 어려운 영역에 대해서도 자신감이 0인 엉터리 추정을 내놓는게 아니라 최대한 그럴듯 하게 추정한 결과를 내놓도록 학습을 이끌 수 있다. 

### Downstream Applications
최종 산출물인 pointmaps을 이용해 해결할 수 있는 문제들은 아래와 같다.
1. Point matching
2. Recovering intrinsics
3. Relative pose estimation
4. Absolute pose estimation
### Global alignment
두 장의 이미지만 받을 수 있는 구조이기 때문에, 여러 이미지를 처리하기 위해선 따로 post-processing 과정이 필요하다.

**Pairwise graph**: 특정 씬에 대한 이미지 셋을 받았을 때, 공유하는 visual content가 있는 이미지 쌍을 찾아 connectivity graph $\mathcal{G}$ 를 만든다. 각 쌍에 대해 $\mathcal{F}$를 통과시키고, 평균 confidence가 낮은 쌍은 제거한다. 

**Global optimization**: 이제 $\mathcal{G}$에는 일정 confidence 이상의 이미지 pair만 존재한다. 이를 이용해 globally aligned pointmaps를 얻고자 한다. 그 결과는 $\chi$로 나타내며 $n$개의 카메라마다 생성되며 기준은 하나의 공통 좌표계이다. 
![[Pasted image 20260811154609.png]]
(by Claude)
이 과정은 [[Structure from Motion]]의 Bundle Adjustment 과정과 비슷한 역할이다.

## Experiments
- 8개의 데이터셋에서 이미지 쌍을 구하는 알고리즘을 적용해 총 8.5M 개의 이미지 쌍을 데이터로 사용했다.
- 224 x 224의 해상도 이미지로 먼저 학습시킨 후 512 x 512 이미지로 학습을 진행했다. 
- CroCo pretraining으로 초기화 했다. 
- 각 배치마다 랜덤하게 aspect ratio를 적용했다(16/9, 4/3 등).

하나의 pointmap을 이용해 다양한 하위 태스크를 수행할 수 있다는 것을 보이기 위한 실험이 진행됐다.
1. Visual Localization
2. Multi-view Pose Estimation
3. Monocular Depth
4. Multi-view Depth
5. 3D Reconstruction
