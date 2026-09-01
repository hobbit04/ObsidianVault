---
title: "VGGT: Visual Geometry Grounded Transformer"
aliases:
  - Wang 2025
  - "VGGT: Visual Geometry Grounded Transformer"
first_author: Jianyuan Wang
year: 2025
venue: CVPR
school:
  - University of Oxford
lab:
  - Meta AI
kind: method
task:
  - 3D reconstruction
  - camera pose
  - depth estimation
  - point tracking
code: https://github.com/facebookresearch/vggt
status: read
pdf: "[[VGGT.pdf]]"
tags:
  - paper
---
[[VGGT.pdf]]

기본적으로 [[DUSt3R]]과 같은 문제를 비슷한 방식으로 해결하려고 한다. 신경망만을 이용해 3D 카메라 정보를 알아내는 것을 목표로 한다. 이미지 두 개만 받을 수 있고 post processing 과정에서야 reconstruction을 할 수 있었던 DUSt3r이나 MASt3r의 한계를 극복한 논문이다. 

## Related work
- [[Structure from Motion]]
- [[Multi View Stereo Reconstruction]]
- [[Tracking Any Point]]

## Method
### Problem definition and notation
- Input: $(I_i)^N_{i=1}$, $N$ 개의 RGB images(sequence)
- Output: $g_i, D_i, P_i, T_i$. 각각 camera parameters, depth map, point map, and grid of $C$-dimensional features for point tracking.
Camera parameters $g_i$의 경우, VGGSfM 논문의 파라미터화 방법을 사용했다. $g=[q,t,f]$ 으로 나타내고 각각 rotation quaternion, translation vector, and the field of view 이다. 
### Feature Backbone
![[Pasted image 20260812101705.png]]
[[DINOv2]]로 $K$개의 토큰으로 패치화 한 후 카메라 토큰을 각 이미지 토큰에 추가한다. 또한 네 개의 register tokens도 추가한다. 이후 두 개의 attention layer를 반복한다. 이를 Alternating-Attention 이라고 이름 붙였다.
**Frame-wise self-attention**: 각 프레임마다 자신의 토큰들 사이에서 self attention을 한다. 
**Global self-attention**: 모든 이미지 토큰을 대상으로 self attention을 한다. 

논문에선 위 두 개의 과정을 $L=24$번 반복하도록 했다. 왜 cross attention보다 self attention이 더 빠르고 좋은 결과가 나왔는지 제대로 설명은 없지만, ablation 실험을 통해 효용성은 입증을 했다.

### Prediction heads
첫 번째 이미지를 기준 이미지로 알리기 위해 토큰에 추가하는 camera token, register tokens를 다르게 준다. 다른 이미지들은 공통의 tokens를 추가해 학습시킨다. 이때 register token의 역할은 [[Vision Transformer|ViT]]를 이해하면 알 수 있다. ViT 학습 시 몇 개의 이미지 토큰을 정보 캐싱을 위한 공간으로 사용하는 현상이 발견돼 이를 위한 공간을 따로 마련한 것이 register tokens 이고, 이 논문에서도 동일한 목적으로 추가한 것이다. 나머지 두 종류의 토큰(image, camera)은 각 head를 통과해 서로 다른 결과물을 만드는데 사용된다.
- Output **camera tokens** $(\hat{t}_i^g)^N_{i=1}$ $\rightarrow$ Camera parameters $(\hat{g}^i)^N_{i=1}$  
- Output **image tokens** $\hat{t}^I_i$ $\rightarrow$ Depth maps $D_i$, point maps $P_i$, tracking features $T_i$
이때 image tokens는 먼저 [[Dense Prediction Transformer|DPT]] layer를 통과해 dense feature maps로 변환된다(Fig. 2 참고). 

또한 [[Aleatoric uncertainty]]도 예측하는데, 각각의 depth / point map에 대해 예측한다. 이는 loss 계산에 활용되고 모델의 confidence를 계산할 때도 사용된다.

**Tracking**을 위해 논문에선 CoTracker2 아키텍쳐를 사용한다. 이 구조의 input인 tracking features를 모델이 내놓도록 설계한 이유다.

### Training
이 모델은 *multi-task loss*를 이용해 학습된다.
$$\mathcal{L}=\mathcal{L}_\text{camera}+\mathcal{L}_\text{depth}+\mathcal{L}_\text{pmap}+\lambda \mathcal{L}_\text{track}$$
Camera, depth, point map의 loss는 범위가 비슷해서 따로 weight을 다르게 하지 않았지만 tracking loss 는 범위가 더 넓어서 $\lambda=0.05$의 값으로 가중치를 줬다.

**Camera loss**
$\mathcal{L}_\text{camera}=\sum_{i=1}^N ||\hat{g}_i - g_i||_\epsilon$ 로 정의된다. 수식을 보면 [[Huber loss]]를 이용해 정의된 것을 알 수 있다.

**Depth loss**
$\mathcal{L}_\text{depth}$는 [[DUSt3R]]과 유사하게 정의한다. 이 논문에선 불확실성(confidence로 볼 수 있음)을 표현하는 식이 $\hat{\Sigma}^D_i$이기 때문에 마지막에 $-\alpha \log \Sigma^D_i$ 항을 추가한 것이다(불확실성에는 어차피 ground truth 값이 존재하지 않기 때문에 $\hat{}$ 표기를 했다가, 안했다가 혼용하는 것 같음). 

*헷갈렸는데, $\Sigma^D_i$가 i개의 D를 더하는 의미가 아니라 그냥 시그마 기호에 위첨자가 $D$ 일 뿐인 것이었다.*
$$\mathcal{L}_\text{depth}=\sum^N_{i=1} ||\Sigma^D_i \odot (\hat{D}_i-D_i)|| + ||\Sigma^D_i \odot (\nabla \hat{D}_i - \nabla D_i)|| - \alpha \log \Sigma^D_i$$위와 같은 수식으로 정의된다. 이때 두번째 항이 DUSt3R과 다른 부분인데, 이는 gradient-based term 이다. 이런 방식은 monocular depth estimation에서 자주 사용되는 방식이라고 한다. 

**Point map**
Depth map과 유사하게 구성된다. $$\mathcal{L}_\text{pmap}=\sum^N_{i=1} ||\Sigma^P_i \odot (\hat{P}_i-P_i)|| + ||\Sigma^P_i \odot (\nabla \hat{P}_i - \nabla P_i)|| - \alpha \log \Sigma^P_i$$
**Tracking loss**
$$\mathcal{L}_\text{track}=\sum^M_{j=1}\sum^N_{i=1}||y_{j,i}-\hat{y}_{j,i}||$$
로 정의된다. 수식을 보면 feature라고 할 수 있는 $T_{j,i}$가 아니라 이를 바탕으로 계산된 각 프레임의 대응되는 2D 픽셀 좌표인 $y_j,i$ 끼리 비교를 시킨다는 것을 알 수 있다. Ground truth 픽셀 좌표를 구하는 방법은 Appendix B에 나와 있다. 

**Visibility loss**
논문에서 언급만 되고, CoTracker2의 것을 그대로 적용했다고 한다. 

### Ground Truth Coordinate Normalization
3차원 scene은 확대/축소를 해도 같은 scene이다. 이런 모호성을 없애기 위해 normalization이 필요하다. 첫번째 카메라의 좌표를 기준으로 각 3D points 의 유클리디안 거리를 재고, 이를 바탕으로 정규화 한다. 이러한 과정은 학습 데이터에만 적용되고, 모델의 output에는 적용되지 않는다. 알아서 모델이 학습하도록 둔다. 

## Experiments
실험은 총 네 가지 항목에 대해 이뤄졌고 ablation 실험도 진행했다. 마지막엔 Downstream Tasks를 위한 Fine tuning 실험도 제시했다.
### Training Data
- Co3Dv2
- BlendMVS
- DL3DV
- MegaDepth
- Kubric
- WildRGB
- ScanNet
- HyperSim
- Mapillary
- Habitat
- Replica
- MVS-Synth
- PointOdyssey
- Virtual KITTI
- Aria Synthetic Environments
- Aria Digital Twin
- Objaverse 와 유사한 데이터 셋
을 종합적으로 사용했다. 
### Camera Pose Estimation
![[Pasted image 20260812164459.png|358]]
Metric: [[AUC]]@30
여기서 AUC@30은 RRA와 RTA를 결합한 지표이다. 30은 곡선 밑의 넓이를 구하는 적분 범위가 $0\degree$~ $30\degree$라는 뜻이다. 
- **RRA (Relative Rotation Accuracy)**: 두 이미지 쌍 사이의 **상대적 회전** 오차를 각도로 계산
- **RTA (Relative Translation Accuracy)**: 두 이미지 쌍 사이의 **상대적 이동(translation)** 오차를 각도로 계산
즉 회전과 이동에 대한 오차를 모두 각도로 계산한다는 뜻이다. 두 지표 중 더 작은 값을 사용한다. 

![[Pasted image 20260812170407.png]]
(by Claude)

이렇게 $A(\tau)$를 정의했다면, $\tau$에 대해 정적분을 해준다(이게 Area Under Curve를 구하는 부분).$$\text{AUC@30}=\frac{1}{30}\int_0^{30}A(\tau)d\tau$$30으로 나눠준 것은 normalization을 위함이다. 실제 계산은 이산적인 공간에서의 적분(리만 합)으로 근사하게 된다. 

이렇게 학습한 VGGT는 최적화 기반의 기법들을 후처리(BA 등) 없이 이길 수 있고, 처음보는 데이터 셋(RealEstate10K)에서 격차가 더 커지는 모습을 확인할 수 있다. 

### Multi-view Depth Estimation
DUSt3R 보다 훨씬 높은 성능을 보인다. 심지어 카메라의 ground-truth 정보를 알고 있는 모델들과 비슷한 성능을 보인다. 

### Point Map Estimation
ETH3D 데이터셋을 이용해 실험한다. 이때 좌표계를 맞춰주기 위해 [[Umeyama algorithm]]을 사용한다. DUSt3R과 MASt3R과 비교해서 훨씬 빠른 시간 내에 더 높은 정확도를 보여준다. 

또한 이 모델의 다른 두 결과인 depth map과 camera head를 이용해 unprojection 하는 방식으로 생성한 point map이 더 높은 성능을 보였다. 

### Image Matching
Tracking accuracy를 평가하기 위해 image matching task를 선택한다. Image matching도 결국 two view tracking으로 볼 수 있기 때문이다. 

특별히 two-view matching에 특화시키지 않았는데도 가장 높은 성능을 보였다. 