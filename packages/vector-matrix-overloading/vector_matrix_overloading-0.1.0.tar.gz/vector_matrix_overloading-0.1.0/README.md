# Vector Matrix Overloading

벡터와 행렬 연산을 위한 연산자 오버로딩 패키지입니다. 직관적인 연산자(`+`, `-`, `*`)를 사용하여 벡터와 행렬 연산을 수행할 수 있습니다.

## 설치

```bash
pip install vector-matrix-overloading
```

## 기능

### Vector (벡터)

- 벡터 덧셈/뺄셈 (`+`, `-`)
- 벡터 내적 (`Vector * Vector`)
- 스칼라 곱 (`Vector * scalar`, `scalar * Vector`)
- 유클리드 노름 (길이)
- 단위 벡터
- 벡터 간 거리 계산

### Matrix (행렬)

- 행렬 덧셈/뺄셈 (`+`, `-`)
- 행렬 곱 (`Matrix * Matrix`)
- 행렬-벡터 곱 (`Matrix * Vector`)
- 스칼라 곱 (`Matrix * scalar`, `scalar * Matrix`)
- 행렬 전치 (`T()`)
- 단위 행렬 생성 (`eye()`)
- 영 행렬 생성 (`zeros()`)
- 행렬식 계산 (`det()`) - 1~3차 정사각행렬 지원

## 사용 예제

### Vector 사용법

```python
from vector_matrix_overloading import Vector

# 벡터 생성
v1 = Vector.of([1, 2, 3])
v2 = Vector.of([4, 5, 6])

# 벡터 덧셈
v3 = v1 + v2  # Vector([5.0, 7.0, 9.0])

# 벡터 뺄셈
v4 = v1 - v2  # Vector([-3.0, -3.0, -3.0])

# 벡터 내적
dot_product = v1 * v2  # 32.0

# 스칼라 곱
v5 = 2 * v1  # Vector([2.0, 4.0, 6.0])
v6 = v1 * 3  # Vector([3.0, 6.0, 9.0])

# 벡터 노름 (길이)
length = v1.norm()  # 또는 abs(v1)

# 단위 벡터
unit_v = v1.unit()

# 벡터 간 거리
distance = v1.distance_to(v2)
```

### Matrix 사용법

```python
from vector_matrix_overloading import Matrix, Vector

# 행렬 생성
A = Matrix.of([[1, 2], [3, 4]])
B = Matrix.of([[5, 6], [7, 8]])

# 행렬 덧셈
C = A + B

# 행렬 뺄셈
D = A - B

# 행렬 곱
E = A * B

# 행렬-벡터 곱
v = Vector.of([1, 2])
result = A * v  # Vector 결과

# 스칼라 곱
F = 2 * A
G = A * 3

# 행렬 전치
A_T = A.T()

# 단위 행렬
I = Matrix.eye(3)

# 영 행렬
Z = Matrix.zeros(2, 3)

# 행렬식
det_value = A.det()  # 1~3차 정사각행렬만 지원
```

## 요구사항

- Python 3.8 이상

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

