---
tags:
  - ComputerVision
  - Metric
---
평가 순서
1. 물체 탐지: Mask2Former 를 이용해서 탐지. confidence threshold가 0.3 이상(어떤 task는 0.9 이상)이어야 해당 물체로 판단
2. (필요한 경우) 위치관계 파악: 최소 얼마정도 떨어져 있어야 판단을 할 수 있고, 탐지된 box의 거리로 측정(left, right, above, below)
3. 색상 탐지: CLIP ViT-L/14 모델을 이용. 
4. 최종 점수 계산: 프롬프트의 지시 사항과 모두 일치하면 1, 하나라도 잘못된 경우 0으로 하여 총 553개의 프롬프트 중 1의 개수를 비율로 나타냄. 

CLIPScore는 이미지의 어떤 부분 때문에 해당 점수가 나왔는지 알 수 없지만 GenEval은 프롬프트와 어떤 부분이 일치하지 않는지 알려줌