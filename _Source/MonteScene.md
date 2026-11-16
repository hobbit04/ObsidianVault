---
School:
  - Graz University of Technology
  - University Paris-Est
title: Monte Carlo Scene Search for 3D Scene Understanding
venue: CVPR
date: 2021-05-05
---
## Task
3D-Scene reconstruction. 구체적으로, RGB-D 카메라로 얻은 [[Point Cloud]]를 이용해서 CAD로 만든 것 같은 3D scene을 얻는 것을 목표로 한다.
![[Pasted image 20261111133006.png|514]]

## Previous Limits
- 지도학습 기반의 시도는 많은 한계점들이 있다. 사람이 직접 annotation을 해야 하는데 여기에 오류가 많이 섞여 있고, 모델의 성능이 annotation 퀄리티에 제한된다. 
- 비지도학습 방법들도 많이 시도가 되었다.
	- Markov Random Fields: 목적 함수에 강한 제약이 있음
	- Conditional Random Fields: 목적 함수에 강한 제약이 있음
	- Markov Chains Monte Carlo: 파라미터 설정에 예민하고 파라미터 수 자체도 많음
	- Tree search: 탐색의 너비가 제한되어 있어 좋은 답을 못찾을 수 있음
	- Hill climbing: Local optimum에 쉽게 갖힘
	등의 방법이 언급되었다. 


## Method
Monte Carlo Scene Search(MCSS)라는 기법을 만들었고 이를 먼저 layout 제안을 생성할 때 사용하고 이후 object 제안을 생성하는데에 사용한다(2-step apply). 