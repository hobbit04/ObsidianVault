---
title: "PointNet: Deep Learning on Point Sets for 3D Classification and Segmentation"
aliases:
  - Qi 2017
  - "PointNet: Deep Learning on Point Sets for 3D Classification and Segmentation"
first_author: Charles R. Qi
year: 2017
venue: CVPR
school:
  - Stanford University
kind: method
task:
  - point cloud
  - classification
  - segmentation
code: https://github.com/charlesq34/pointnet
status: queued
pdf: "[[PointNet.pdf]]"
tags:
  - paper
---
[[PointNet.pdf]]

이 논문은 [[Point Cloud]] 데이터를 딥러닝으로 직접 처리한 최초의 논문으로 볼 수 있다. 
![[Pasted image 20260814131957.png]]

기존에 문제가 됐던 것은 point cloud가 근본적으로 Irregular하고 Unordered 하다는 것이었다. 딥러닝은 이를 받아들일 수 없기 때문에 이 논문에서는 max pooling을 하는 방식으로 이를 해결하고자 한다. 
아키텍쳐를 보면 input이 $n \times 3$인 것을 알 수 있다. 총 $n$개의 점들로 이루어진 point cloud가 있을 때, 각 점들은 3차원 좌표(벡터)를 가지므로 $n\times 3$으로 나타나는 것이다. 이때 각 점은 위치 뿐만 아니라 색상이나 법선벡터([[Normal]])를 가질 수도 있다. 이 경우에는 $n\times 6$, $n\times 9$등으로 표기할 수 있다. 