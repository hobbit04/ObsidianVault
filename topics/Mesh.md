---
tags:
  - 3D
  - ComputerVision
  - 3D_Representation
---
Mesh는 [[Point Cloud]]에 면을 부여한 표현이다. Mesh의 representation은 여러가지가 있지만, 가장 널리 사용되는 방법은 Face-vertex meshes이다.

## 정의
[![Figure 3. Face-vertex meshes|441](https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Mesh_fv.jpg/500px-Mesh_fv.jpg?utm_source=en.wikipedia.org&utm_campaign=parser&utm_content=thumbnail)](https://en.wikipedia.org/wiki/File:Mesh_fv.jpg "Figure 3. Face-vertex meshes")
Face를 표현하는 방법은 위 figure의 Face List를 보면 알 수 있다. 각 면(face)마다 세 개의 점(vertices, v)이 저장된 것을 볼 수 있는데, 삼각형(polygon)이 면을 구성하는 기본 요소이기 때문이다. 
Vertex List에는 어떤 점이 포함된 면들을 저장한다. v5를 보면 총 5개의 면, f0, f1, f2, f8, f9에 포함되어 있기 때문에 해당 면들이 List에 저장되어 있는 것이다. 

정리하면 $M = (V, F)$ 로, vertices $V \in \mathbb{R}^{n\times3}$ 와 faces $F \in \mathbb{N}^{m\times3}$ 의 쌍이다. $n$은 vertex의 개수, $m$은 faces의 개수를 의미한다. 위의 예시에서 $n=10,m=16$이다. 

이때 corner라는 개념도 등장한다. Corner는 (Face + vertex) 쌍을 의미한다. 

## 속성
Vertex나 face에 좌표 외의 정보를 붙일 수 있다.
- [[Normal]]: Face normal과 vertex normal. Point cloud와 달리 정점 순서(winding order)로 방향이 결정되므로 부호 모호성이 없다. Face *List*라 순서가 중요함(`[0, 1, 2]`와 `[0, 2, 1]`은 순서가 달라 다른 방향을 가리킴). Vertex normal은 인접한 face normal 들의 가중 평균이다. 가중치로는 face의 넓이 등을 사용할 수 있다.
- [[UV coordinate|UV]] 좌표: 사용할 Texture 이미지의 어떤 부분에 대응되는지에 대한 정보를 corner에 저장한다. 면 내부의 색은 세 정점의 UV를 barycentric 좌표로 보간해 가져온다. Vertex가 아니라 corner 단위인 이유는 seam 때문이다. 표면을 평면에 펼치려면 어딘가는 잘라야 하는데, 그 경계의 정점은 면마다 다른 UV를 가져야 한다. 그래서 `.obj`는 `f v/vt/vn` 형식으로 위치, UV, normal의 인덱스를 각각 따로 저장한다.
- Vertex color: 텍스쳐를 사용하는 대신 vertex 자체에 색상을 부여한다. UV unwrapping이 필요 없어 간단하지만, 색의 해상도가 mesh 밀도에 종속된다(정점이 1만 개면 색도 1만 개). 면 내부는 보간만 되므로 선명한 패턴도 표현할 수 없다. 3D 스캔이나 재구성 결과물처럼 unwrapping을 거치기 어려운 경우에 주로 쓰인다.
- Material: 빛 반사를 어떻게 할지에 대한 정보를 담은 함수가 있는데, 그런 함수들 중 어떤 함수를 참조할지에 대한 정보를 face에 저장한다. 함수의 형태([[BRDF]])는 material이 정하고, 지점마다 달라지는 파라미터 값(albedo, roughness, metallic 등)은 texture가 담당한다. 즉 texture는 material의 파라미터를 공간적으로 변화시키는 수단이다.

| 단위     | 개수        | 담는 것                |
| ------ | --------- | ------------------- |
| Vertex | $n$       | 위치, vertex color    |
| Corner | $3m$      | UV, vertex normal   |
| Face   | $m$       | material 인덱스        |
| Texel  | $1024^2$등 | material 파라미터의 실제 값 |

## 위상 (Topology)
- **Manifold**: 모든 지점이 국소적으로 평면처럼 생겼는가
- **Watertight**: 구멍 없이 닫혀 있는가 → 부피 계산, 물리 시뮬레이션, 3D 프린팅의 전제
- **Genus**: 구멍의 개수. 

## 획득 방법
크게 두 갈래다. 점을 **직접 잇는** 방식과, 점을 **함수로 바꾼 뒤 등위면을 뽑는** 방식이다.

| 경로                                                   | 방법                                                 | 성격                                    |
| ---------------------------------------------------- | -------------------------------------------------- | ------------------------------------- |
| [[Point Cloud]] → Mesh                               | [[Ball-pivoting]], [[Alpha shape]]                 | 점을 직접 연결. 원본 보존에 유리하나 노이즈와 밀도 불균일에 취약 |
| [[Point Cloud]] → Mesh                               | [[Poisson surface reconstruction]] ([[Normal]] 필수) | 함수화 후 등위면 추출. 노이즈에 강하고 항상 watertight  |
| [[Voxel]] / [[Signed Distance Function\|SDF]] → Mesh | **[[Marching Cubes]]**                             | implicit에서 explicit으로 넘어오는 표준 통로      |
| 직접 제작                                                | CAD, 3D 모델링 툴                                      | artist-created mesh. 면 수가 적고 quad 위주  |
파일 포맷은 `.obj`, `.ply`, `.stl`, `.glb` 등이 쓰인다.

## 표현으로서의 특징
**장점**
- 표면이 명시되어 있어 렌더링, 음영, 텍스처 매핑이 가능하다
- 적은 데이터로 매끄러운 표면을 표현한다([[Voxel]]의 $O(n^3)$ 과 대비)
- 부피와 표면적을 계산할 수 있다
- 그래픽스 파이프라인의 표준으로, GPU가 삼각형을 직접 처리한다

**한계**
- 위상을 바꾸기 어렵다(구멍을 뚫거나 두 덩어리를 합치는 일)
- Point cloud의 unordered / irregular 문제를 물려받는다
- Self-intersection, non-manifold 같은 불량 형상이 생기기 쉽다
- 출력 크기가 가변적이라 신경망의 출력으로 삼기 까다롭다

## 전처리 과정과 평가
재구성으로 생성된 mesh는 그대로 쓰기 어려워서, 전처리 과정을 거친다.
- **Simplification / Subdivision / Remeshing**: 해상도와 face 품질 조절
- **Smoothing(Laplacian), hole filling**: 노이즈 제거, self-intersection 해소 등 정합성을 복구하는 과정

**지표**: mesh 표면에서 점을 샘플링한 뒤 [[Chamfer distance]], [[F-score]]로 비교한다. 결국 point cloud 지표로 환원된다는 점이 특징이고, 여기에 normal consistency를 더한다. Normal consistency는 대응되는 점들의 normal의 내적 평균을 뜻한다. 같은 방향이면 내적 값이 클 것이고, 다른 방향을 가리킬 수록 값이 작아지기 때문에 이 값은 클 수록 좋은 지표이다. 

## 참고
- https://youtu.be/TDic3pJyYb8
- https://en.wikipedia.org/wiki/Polygon_mesh#File_formats
- https://en.wikipedia.org/wiki/Vertex_normal