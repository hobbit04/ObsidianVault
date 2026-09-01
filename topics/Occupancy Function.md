---
tags:
  - 3D
  - ComputerVision
---
공간의 각 점이 물체 내부인지 외부인지를 나타내는 함수. $$o(x)=\begin{cases}1 & \text{물체 내부}\\
0 & \text{물체 외부}
\end{cases}$$
위와 같이 단순한 형태의 *Binary Occupancy* 도 있지만, 0과 1사이의 확률을 저장하는 *Probabilistic Occupancy* 함수도 있다. "해당 위치가 물체 내부일 확률이 $0.9$다" 같은 식의 정보를 담고 있는 것이다. 이 함수 자체는 implicit한 방식으로 3d representation을 하지만, 이를 [[Voxel]]에 저장하면 explicit 하게도 사용할 수 있다. 

[[Signed Distance Function|SDF]]와는 자명한 관계를 갖고 있는데, SDF가 음수인 영역은 $o(x)$가 1이고, 양수인 영역은 0으로 나타날 것이다. 

Occupancy function은 gradient 등은 이용하기 어렵지만(binary의 경우) 메모리를 적게 차지하고 단순하다는 장점을 가진다. 

### Neural Occupancy
[[Occupancy Networks]]에서 제시된 방법이 대표적으로, 신경망이 함수 $o(x)$를 직접 학습하도록 하는 방법이다. 