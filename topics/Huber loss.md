---
tags:
  - LossFunction
---
회귀 문제에서 손실 함수로 사용하며, [[L1 loss]] 와 [[L2 loss]] 를 결합해 두 방식의 단점을 보완하고자 하는 시도다.

구간을 나눠 정의되며 오차 $x$가 $\epsilon$보다 작거나 같은 경우 L2 loss 처럼 동작하고 더 큰 경우 L1 loss  처럼 동작하게 된다.
![[Pasted image 20260812143055.png|255]]

이는 오차가 클 때 L2 loss 가 이를 극대화 시키는 단점, 즉 outlier에 너무 예민하게 반응하는 단점을 보완하고 L1 loss 가 0근처에서 gradient가 진동하기 쉽다(+1, -1 둘 중 하나만 가능하니)는 단점을 보완하는 방식이다. 

## Reference
https://en.wikipedia.org/wiki/Huber_loss