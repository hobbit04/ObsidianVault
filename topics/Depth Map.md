---
tags:
  - 3D
  - ComputerVision
  - 3D_Representation
---
## 정의
이미지의 각 픽셀에 3d 모델의 표면과 카메라로부터의 거리 값을 저장한 표현 방식. 가까울수록 밝고 멀수록 어두운 형식의 흑백 이미지로 표현한다. 

저장되는 depth의 종류에 따라 두 가지 방식이 있다.
1. **Z-depth**: 카메라 광축 방향의 성분 $Z$를 저장하는 방식
2. **Ray depth**: 카메라 중심에서 점까지의 실제 유클리드 거리를 저장하는 방식으로, LiDAR 등을 사용할 때 사용한다.
Z-depth 방식과 달리 Ray depth 방식은 등고면이 구면이 된다. 특히 이미지 외각으로 갈 수록 두 방식의 차이가 커질 수밖에 없다. 

$Z$는 카메라 좌표계를 기준으로 3D 점의 좌표를 복원하면 얻을 수 있다. 또는 rectified stereo 상황에서 두 대의 카메라를 이용해 시차를 두고 촬영하면 $Z=\frac{fB}{d}$의 수식으로 구할 수 있다. ($d$는 시차, $B$는 baseline, $f$는 focal length)

## Point cloud와의 관계
Depth map과 Intrinsic parameters를 알고 있으면 [[Point Cloud]]를 얻을 수 있다.
$$X=d(u,v)K^{-1}[u \ v\ 1]^T$$
이때 $d(u, v)$가 depth map, $K$가 intrinsic parameters다. 

## 손실 함수와 평가
### Loss
- [[Scale-invariant log loss]]
- [[BerHu loss]]
- [[Huber loss]]
- Gradient matching loss
- SSIM+L1 photometric
### Metric
- [[AbsRel]]
- [[RMSE]]
- RMSE-log
- $\delta_i$

## 한계
- Occlusion: 카메라 시점에서 보이는 표면만 기록하기 때문에 뒷면에 대한 정보는 없다. 그래서 depth map을 2.5D 표현이라고 부르기도 한다.
- Scale ambiguity: 이미지 하나에서 얻은 정보기 때문에 스케일을 알 수 있는 방법이 없다.
- Discontinuity: 물체 경계에서 flying pixels가 발생해 point cloud로 변환할 때 노이즈가 생긴다. 