---
tags:
  - 3D
  - ComputerVision
  - 3D_Representation
---
3차원 공간상의 점들을 모아놓은 집합으로 3D 데이터를 표현하는 방식이다. 가장 단순하고, 센서나 [[Structure from Motion|SfM]] 파이프라인이 가장 먼저 만들어내는 형태이기 때문에 다른 모든 3D 표현의 출발점이자 공통 인터페이스 역할을 한다.

## 정의
$n$개의 점을 갖는 point cloud는 $P \in \mathbb{R}^{n \times 3}$ 인 행렬로 표현된다. 각 행이 점 하나이고, 3개의 열은 그 점의 $x, y, z$ 좌표다.

$$P = \begin{bmatrix} 0.12 & -1.30 & 2.05 \\ 1.44 & 0.08 & -0.71 \\ -0.35 & 2.19 & 1.02 \\ & \vdots & \end{bmatrix}$$
위 행렬을 보면 첫 번째 열인 $(0.12, -1.30, 2.05)$ 가 곧 첫 번째 점의 좌표를 의미한다는 것을 알 수 있다.

표기가 비슷해 이미지의 $H \times W \times 3$ 과 헷갈리기 쉬운데, 둘의 3은 의미가 완전히 다르다.

| | 앞 차원 | 뒤의 3 |
| --- | --- | --- |
| 이미지 $H\times W \times 3$ | **격자 위치** (구조 있음) | **색** (RGB) |
| Point cloud $n \times 3$ | **그냥 목록** (구조 없음) | **위치** (XYZ) |

이미지는 위치가 배열의 인덱스에 암묵적으로 담겨 있지만, point cloud는 위치가 **값으로** 들어있다. 이 차이가 아래에서 이야기할 unordered, irregular 문제의 근원이다.

## 속성
좌표 외에 점마다 추가 정보를 붙일 수 있고, 그러면 열이 늘어난다($n\times6$, $n\times9$ 등). 대표적인 것이 color와 normal이다.

### Color
각 점의 RGB 값이다. RGB-D 카메라나 MVS처럼 이미지에서 유래한 point cloud는 자연스럽게 색을 갖는다. 반면 LiDAR는 색 대신 intensity(반사 강도)를 준다.

### Normal
![[Normal]]

[[Mesh]]는 face가 있어서 표면의 방향이 정점 순서에서 자동으로 결정되지만, point cloud는 점만 있어서 표면 방향 정보가 없다. Normal은 그 잃어버린 정보를 복원해 붙여주는 장치다.

**부호 모호성**: 위 방법은 방향만 알려줄 뿐 부호를 정해주지 못한다. $\mathbf{n}$과 $-\mathbf{n}$ 둘 다 표면에 수직이기 때문이다. 따라서 추정 직후에는 어떤 점은 바깥을, 어떤 점은 안쪽을 향하는 상태이며 이를 일관되게 맞춰주는 과정이 필요하다.
- 카메라 위치를 아는 경우 카메라 쪽을 향하도록 뒤집는다(그 점이 보였다는 것은 그 면이 카메라를 향했다는 뜻이다). SfM/MVS 결과물에는 카메라 정보가 있으므로 이 방법이 자연스럽다.
- 또는 최소 신장 트리([[MST]])를 따라 이웃끼리 부호를 전파시킨다.

**쓰임새**: 음영 계산($\max(0, \mathbf{n}\cdot\mathbf{l})$), Poisson surface reconstruction(normal이 **필수 입력**이다), point-to-plane [[ICP]], 평면/모서리 검출 등에 사용된다.

## 획득 방법
| 출처                                   | 특징                                              |
| ------------------------------------ | ----------------------------------------------- |
| LiDAR                                | 센서가 직접 측정. metric scale을 가짐. 색은 없고 intensity를 줌 |
| Depth camera (RGB-D)                 | depth map을 unprojection해서 얻음. 색을 함께 가짐          |
| [[Structure from Motion]]            | **Sparse**. 수천~수만 점. feature가 매칭된 지점에만 점이 생김    |
| [[Multi View Stereo Reconstruction]] | **Dense**. 수백만 점. 거의 모든 픽셀이 3D 점이 됨             |

Sparse인지 dense인지가 이후 쓰임새를 가른다. Sparse point cloud는 카메라 pose 추정의 부산물에 가깝고 형상을 보기엔 부족하지만, [[3D Gaussian Splatting]]의 초기화처럼 씨앗으로 쓰기에는 충분하다. 형상 자체를 다루려면 dense가 필요하다.

파일 포맷으로는 `.ply`, `.pcd`, `.las`/`.laz`(측량 분야), `.xyz` 등이 쓰인다.

## 표현으로서의 특징
**장점**
- 표현이 단순하고 센서/알고리즘 출력과 직결된다
- 임의의 topology를 표현할 수 있다(닫힌 면, 열린 면, 복잡한 형상 모두)
- 점을 추가/삭제하기 쉽고 해상도를 자유롭게 조절할 수 있다

**한계**
- **Connectivity가 없다.** 점들 사이의 연결 관계, 즉 면(face)이 없다. 따라서 그 자체로는 표면을 렌더링하거나 음영을 줄 수 없고, 부피나 표면적도 계산할 수 없다. 
- **밀도가 불균일하다.** 카메라에 가까운 부분은 촘촘하고 먼 부분은 성기다(스캐닝 방식으로 얻는 경우).
- **구멍이 있다.** Occlusion(가려진 영역)이나 텍스쳐가 없는 영역(하늘, 흰 벽)에는 점이 생기지 않는다.
- 노이즈와 outlier가 섞여 있다.
- Monocular 기반으로 얻은 경우 절대 scale을 알 수 없다.

## [[Shuzhe Wang 2024|Pointmap]]과의 비교
[[Shuzhe Wang 2024|DUSt3R]]의 pointmap $X \in \mathbb{R}^{W \times H \times 3}$ 은 뒤의 3이 point cloud와 똑같이 XYZ이지만, 앞 차원이 이미지 격자다.

| | Point cloud $n\times3$ | Pointmap $W\times H\times3$ |
| --- | --- | --- |
| 구조 | 없음 (unordered, irregular) | 이미지 격자에 정렬됨 |
| 순서의 의미 | 없음 | 있음 (픽셀 대응 관계) |
| CNN/ViT 적용 | 불가 | **가능** |
| 필요한 구조 | [[Charles R. Qi 2017\|PointNet]] 같은 특수 설계 | 기존 2D 백본 그대로 |

즉 **pointmap은 구조를 가진 point cloud**다. 아래에서 설명할 "irregular해서 CNN을 쓸 수 없다"는 문제를, pointmap은 격자 구조를 유지함으로써 우회한다. DUSt3R나 [[Jianyuan Wang 2025|VGGT]]가 ViT로 3D 좌표를 직접 회귀할 수 있는 이유가 여기에 있다.

$W\times H\times3$ 을 flatten하면 $n\times3$ point cloud가 되지만(이때 픽셀 이웃 관계라는 정보를 잃는다), 그 역방향은 카메라 정보 없이는 불가능하다.

## 기본 연산과 평가 지표
**연산**
- **Voxel downsampling**: 공간을 격자로 나누고 각 칸의 점들을 대표점 하나로 합친다. 점 개수를 줄이면서 밀도를 균일하게 만드는 효과가 있다
- **최근접 이웃 탐색**: KD-tree나 octree로 가속한다. normal 추정, 정합, 필터링 등 대부분의 연산의 기반이 된다
- **Outlier removal**: statistical / radius 기반 필터
- **[[ICP]] (Iterative Closest Point)**: 두 point cloud를 정합하는 대표 알고리즘. normal이 있으면 point-to-plane 방식을 쓸 수 있어 수렴이 훨씬 빠르다

**지표**: 3D 재구성 결과는 대부분 point cloud로 변환한 뒤 비교하므로, 아래 지표들은 앞으로 볼 거의 모든 3D 논문의 실험 표에 등장한다.
- **[[Chamfer distance]]**: 각 점에서 상대 집합의 최근접 점까지 거리의 평균. 가장 널리 쓰인다
- **[[Hausdorff distance]]**: 최댓값 기반이라 outlier에 민감하다
- **[[F-score]]: 특정 임계값 이내로 맞은 점의 비율

## 딥러닝 적용의 어려움
Point Cloud는 '60년대 레이저 거리측정 기술에서 기원했고, LiDAR의 발전과 함께 80년대 이후 본격적으로 활용되기 시작했다. 당시엔 딥러닝이 아니라 computational geometry 기반으로 처리하던 데이터였다. 이후 2010년에 Point Cloud Library라는 point cloud 처리를 위한 오픈소스 라이브러리가 등장하며 feature descriptor, segmentation, filtering 알고리즘들이 정립되었다. 이 시기까지 point cloud는 hand-crafted feature + 기하학 알고리즘의 조합으로 다뤄졌다.
[[Johannes L. Schonberger 2016]]의 COLMAP은 딥러닝 없이 기하학적 최적화만으로 point cloud를 만들어내는 대표적인 사례다(SfM 단계에서 sparse point cloud와 카메라 파라미터를, MVS 단계에서 dense point cloud를 출력한다).

Point cloud를 딥러닝의 대상으로 직접 다루지 못한 이유는 크게 두 가지다.
1. Unordered
2. Irregular
위 두 가지가 왜 문제인지 알아보자. 

### Unordered의 문제점
Point cloud는 점들의 "집합"이라, 정해진 순서가 없다. 하지만 신경망은 input의 순서에 따라 결과가 달라진다. 몇번째 weight을 어떤 input에 곱할지가 이미 정해져 있기 때문에, 집합의 원소의 순서가 달라지면 같은 집합이더라도 신경망의 결과가 달라진다. 만약 $n$개의 원소가 있다면 $n!$의 조합에 대해 모두 같은 결과가 나오도록 신경망을 훈련시켜야 할텐데, 이는 사실상 불가능하다. 
수학적으로 말하자면 point cloud는 **permutation invariant**한 함수로 처리돼야 한다. 하지만 신경망(MLP, CNN, RNN, LSTM 등등)은 그러한 성질이 없어서 point cloud를 처리하기는 어렵다.
### Irregular의 문제점
먼저 어떤 데이터가 **regular하다는** 것은, 데이터를 이루는 요소들이 고정된 구조를 갖고 배치되어 있다는 뜻이다. 따라서 이미 정해진 구조를 알고, 데이터 포인트의 위치를 알면 그 이웃이나 순서 등을 알 수 있는 형식을 말한다. 대표적인 구조가 **grid**다. 
Point cloud가 irregular 하다는 것은 이러한 구조가 없다는 것이다. 이는 **CNN을 사용할 수 없다는 문제**로 이어진다. CNN은 regularity를 전제로 convolution kernel 연산을 수행한다. 데이터의 순서가 곧 공간상의 위치로 해석될 수 있다는 전제가 있기에 conv 연산이 가능한 것이다. 
하지만 irregular 한 point cloud는 이웃한 인덱스의 데이터 포인트가 3차원 공간에서도 이웃한다는 보장이 없기 때문에 CNN을 적용할 수 없다. 

### 우회 방법
두 가지 문제를 갖고 있는 point cloud에 딥러닝을 적용시키기 위해 여러 우회 방법들이 제시됐었다. [[Voxel]]로 변환한 다음 3D CNN을 적용하는 방법, 3D point cloud를 이용해 여러 각도에서 2D로 렌더링한 후 2D CNN으로 처리하는 방법 등이 그 예시다. 
### 딥러닝 도입
이러한 변환 없이 딥러닝의 input으로 쓸 수 있는 방법을 고안한 논문이 [[Charles R. Qi 2017|PointNet]]이다.

## 이후 연결
- [[3D Gaussian Splatting]]은 각 점에 공분산, 불투명도, SH 계수를 붙인 point cloud로 볼 수 있다. 초기화도 COLMAP의 sparse point cloud를 사용한다.
- Point cloud의 한계(connectivity 없음)를 메우는 표현이 [[Mesh]]이고, 그 변환을 위해 normal이 필요하다.
