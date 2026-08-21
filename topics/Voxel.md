2차원 픽셀을 3차원으로 옮겨온 것이 Voxel이다. Volumetric Pixel을 줄여서 만든 단어이다. 

## 정의
Voxel은 위치를 정수 인덱스로 나타낸다. [[Point Cloud]]에서 위치를 좌표로 표현한 것과 대조되는 점이다. 
$$V\in \mathbb{R}^{D\times H \times W \times C}$$
이때 $C$는 채널 수로, 어떤 데이터를 담을지에 따라 결정된다. 픽셀이 틀을 제공하고 안에 담기는 값이 rgb인지 흑백인지 등에 따라 채널의 수가 달라졌던 것과 마찬가지로, voxel에도 다양한 값이 담길 수 있다. 
- [[Occupancy Function]]
- [[Signed Distance Function]]


## 특징
| 장점  | Regularity가 보장돼 3D CNN 사용 가능                    |
| --- | ----------------------------------------------- |
| 단점  | 메모리가 $O(n^3)$로 증가하는데 표면은 $O(n^2)$로 증가(sparsity) |
|     | 부드러운 곡선 표현 어려움                                  |
