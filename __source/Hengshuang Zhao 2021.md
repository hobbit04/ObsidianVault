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
### Position Encoding
원래 트랜스포머에서는 어텐션 연산이 permutation invariant해서 토큰의 순서를 부여하기 위해 도입되었지만, 여기서는 공간적인 정보를 주기 위해 사용한다. 

논문에서 제시된 PE는 기존의 PE들(sin, cos 이용)과 달리 신경망으로 학습된다. $$\delta=\theta(p_i-p_j)$$즉 point 들의 위치의 차이를 입력으로 받아 신경망을 통과시킨 뒤 그 값을 PE로 활용한다. 
### Point Transformer Block
![[Pasted image 20260824112257.png|214]]
위 그림과 같이 residual한 연결을 사용한다. 입력, 출력으로 $(x, p)$를 모두 받기 때문에 이 블록은 포인트의 feature와 위치를 모두 활용한다고 볼 수 있다.
### Network Architecture
![[Pasted image 20260824112614.png]]Task의 종류에 맞게 아키텍쳐를 다르게 적용했다. 두 구조 모두 5개의 블록을 통과시켜 일종의 feature encoder를 구성한다. 이후엔 task에 따라 달라지게 되는데, Point Transformer Block에 추가로 Transition Down/Up 블록과 Global AvgPooling 블록이 있는 것을 볼 수 있다. 
![[Pasted image 20260824112736.png]]
위 두 블록의 목표는 2D CNN의 계층적 구조를 구현하는 것이다. 2D CNN에선 Conv, Pooling을 이용해 채널의 수를 깊게 만들었다가 다시 얕게(원본 이미지는 3채널로 얕음) 만들어 계층적으로 특징을 추출할 수 있었다. Point cloud에선 conv, pooling이 불가능(irregular 한 데이터기 때문)하므로 이 역할을 transition down/up block에 맡긴다.
- Transition Down: 점의 수를 1/4로 줄이고(FPS 이용), kNN을 수행해 각 점의 이웃을 선택한다. 이웃들의 feature를 MLP 통과시켜 채널 수가 증가된 feature로 바꾸고, 채널 축으로 max pooling을 해 이웃들의 정보가 담기면서도 채널 수가 증가된 하나의 feature를 얻는다. $\rightarrow$ 점의 수는 감소, 채널 수는 증가
- Transition Up: 이 블록은 segmentation task를 위해 설계된 U-Net 구조에서 필요하다. Encoder, Decoder block으로 나눠서 보면 인코더에는 더 많은 수의 점이 있지만 feature의 깊이가 얕아 표현력이 부족한 정보가 있다. 디코더에는 더 적은 수의 점이 있지만 풍부한 feature를 갖고 있다. 목표는 인코더에 있는 모든 점들의 feature를, 풍부한 디코더의 정보를 이용해 업데이트 하는 것이다. 이를 U-Net으로 연결하면 원본과 동일한 수의 point와 풍부한 feature를 모두 얻을 수 있다. 먼저 feature를 같은 채널 수로 맞춰주고, 인코더의 점을 하나 골라 디코더 점들 중 가장 가까운 세 개를 선택한다. 그들의 feature를 거리의 역수로 가중 평균(interpolation). 이후, 디코더에서 얻은 원본 feature에 MLP를 통과시킨 벡터를 interpolate한 벡터와 더한다.

Head는 task에 따라 다르다.
- Segmentation head: MLP 통과 시켜 Logit 구하기
- Classification head: Global Average Pooling을 한 후 MLP 통과 시켜 Logit 구하기

## Experiments
### Dataset
- 3D Semantic Segmentation: **Stanford Large-Scale 3D Indoor Spaces**, 줄여서 **S3DIS** 라고 하는 데이터 셋을 사용했다. 
- Classification: **ModelNet40** 데이터 셋을 사용했다. 
- Object Part Segmentation: **ShapeNetPart** 데이터 셋을 사용했다.
### Loss function
일반적인 Cross Entropy를 사용한다. Logit과 정답 One-hot vector의 비교.
### Metric
-  3D Semantic Segmentation:**mIoU**, **mAcc**, **OA**
- Classification: **OA**, **mAcc**
- Object Part Segmentation: **instance mIoU**, **category mIoU**

각 metric에 대한 간단한 설명이다(추후 별도 노트 작성 필요).
- **OA**: Overall Accuracy. (맞힌 점) / (전체 점)
- **mAcc**: Class 별 recall의 평균이다. 
- **mIoU**: mean Intersection over Union의 약자. 위 세개의 Semantic segmentation metric 중 가장 엄격한 잣대고 이 논문에서 SOTA를 주장한 것도 이 점수가 잘 나와서이다.
- **instance mIoU**: 각 instance마다 평균 shape IoU를 계산하고 모든 instance에 대해 평균을 내는 방식.
- **category mIoU**: 카테고리별로 