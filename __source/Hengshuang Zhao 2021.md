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
[[Vector Attention]]이라는 것을 사용해 [[Point Cloud]]를 처리한다. Vector Attention은 저자가 주장하는 셀프 어텐션의 두 종류 중 하나로, value와 같은 차원의 가중치 벡터를 생성해서 각 feature마다 중요도를 다르게 두어 value와 곱할 수 있도록 하는 어텐션 방식이다. Scalar Attention에서는 query와 key 벡터를 내적시켜서 하나의 값으로 만드는, 차원을 유지하지 못하는 연산을 수행시켜 feature마다 중요도를 다르게 둘 수는 없었다.
두 과정의 중간이 Multi head attention이고, 헤드의 수 $h$가 feature 차원 $d$와 같도록 극단적이게 둔 것이 Vector attention이다. 

Point cloud는 근본적으로 집합이기 때문에, 순서가 상관없는 self-attention과 궁합이 좋다. 또한 Vector attention을 사용하며, 정확한 어텐션 수식은 다음과 같다. $$y_i=\sum_{x_j\in \chi(i)}\rho(\gamma(\varphi(x_i)-\psi(x_j)+\delta))\odot (\alpha(x_j)+\delta)$$Query와 key의 차이 벡터에 positional encoding을 더하고 softmax를 취한 뒤 value에 positional encoding을 더한 벡터와 point-wise 연산을 수행해 $y_i$를 얻는다. 여기서 집합 $\chi (i)$는 전체 $\chi$의 부분집합으로, $i$번째 대상과 근접한, kNN 집합이다. 이 수식을 기반으로 하나의 Point transformer layer를 다이어그램으로 나타내면 아래와 같다. ![[Pasted image 20260823205854.png]] 여기서 $p$는 점의 위치 position이고, 오직 $\delta$를 계산할 때만 관여된다.  