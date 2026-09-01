---
tags:
  - ComputerVision
  - Metric
---
## PSNR
---
생성된 이미지의 품질을 원본과 비교해서 손실 정보를 측정.
$$10\log_{10}(\frac{R^2}{\text{MSE}})$$
MSE가 0, 즉 완전히 동일한 이미지의 경우 PSNR 값이 정의되지 않는다. R이 0인 경우도 마찬가지인데, R은 픽셀의 최대값을 의미하므로 그럴 일은 거의 없다. 
단점: 사람이 눈으로 봤을 때 얼마나 품질이 좋냐와는 다르기 때문에, 해당 지표에서 높은 성능이 나와도 사람 눈에 어색할 수 있다.
## SSIM
---
PSNR의 단점을 해결하고자 사용되는 지표로, Luminance, Contrast, 그리고 Structural 관점에서 이미지의 품질을 평가한다. 
한계: PSNR 보다는 낫지만, 얘도 사람의 생각과 일치하지 않을 수 있다. 
## LPIPS
---
L2 거리로 유사도를 측정하는데, 잘 학습된 CNN의 layers에서 추출한 feature space에서 비교를 진행한다. 즉 conv, pooling layer를 통과시킨 결과를 비교한다. 
$$\text{LPIPS}(x, y)=\sum_l w_l\cdot ||f_l(x) - f_l(y)||^2_2$$
$f_l$은 CNN의 $l$번째 layer의 feature map이다. $w_l$은 사람의 주관적 평가와 일치하도록 학습된 weight이다. 

- 작을수록 두 이미지가 perceptually 유사함
- PSNR/SSIM과 달리, 구조적 변화나 블러에도 덜 민감
- 특히 style 변화나 texture, 고주파 정보에 민감하게 반응
## FID
---
단일 이미지 쌍을 비교하는 것이 아니고, 이미지 set 간의 분포 차이를 측정하는 metric이다. 
$$\text{FID}(X, Y)=||\mu_X - \mu_Y||^2+\text{Tr}(\Sigma_X + \Sigma_Y-2(\Sigma_X\Sigma_Y)^{1/2}$$
$\mu, \Sigma$: 평균과 공분산(covariance)
$X$: 생성 이미지
$Y$: 실제 이미지

- 작을수록 좋음: 생성 이미지의 분포가 실제 이미지와 비슷함
- 전반적인 distribution shift (mean/variance mismatch)에 민감
- mode collapse, blur, texture shift 등을 감지하는 데 효과적