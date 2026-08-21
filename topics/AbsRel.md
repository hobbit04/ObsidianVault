---
tags:
  - Metric
---
Absolute Relative Error을 뜻하며, $y_\text{gt}$와 $y_\text{pred}$ 가 있을 때 수식은 $$\text{AbsRel}=\mathbb{E}[\frac{|y_\text{pred}-y_\text{gt}|}{y_\text{gt}}]$$으로 나타난다. 즉 오차의 절댓값을 정답값으로 나눈 후 평균을 측정한다. 