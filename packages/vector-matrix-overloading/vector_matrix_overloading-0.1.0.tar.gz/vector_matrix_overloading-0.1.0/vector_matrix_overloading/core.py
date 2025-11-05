from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Tuple, Union
import math

Number = Union[int, float]

#Vector Overloading
@dataclass(frozen=True)
class Vector:
    _coords: Tuple[float, ...]

    # --- 생성자 유틸 ---
    @staticmethod
    def of(values: Iterable[Number]) -> "Vector":
        coords = tuple(float(v) for v in values)
        if len(coords) == 0:
            raise ValueError("차원이 0인 벡터는 허용하지 않습니다.")
        return Vector(coords)

    # --- 기본 프로토콜 ---
    def __len__(self) -> int:
        return len(self._coords)

    def __iter__(self):
        return iter(self._coords)

    def __getitem__(self, i: int) -> float:
        return self._coords[i]

    def __repr__(self) -> str:
        return f"Vector({list(self._coords)})"

    # --- 내부 검증 ---
    def _check_same_dim(self, other: "Vector"):
        if len(self) != len(other):
            raise ValueError(f"차원 불일치: {len(self)}D vs {len(other)}D")

    # --- 연산자 오버로딩 ---
    def __add__(self, other: "Vector") -> "Vector":
        self._check_same_dim(other)
        return Vector.of(a + b for a, b in zip(self, other))

    def __sub__(self, other: "Vector") -> "Vector":
        self._check_same_dim(other)
        return Vector.of(a - b for a, b in zip(self, other))

    def __mul__(self, other: Union["Vector", Number]) -> Union["Vector", float]:
        # Vector * Vector  → 내적
        if isinstance(other, Vector):
            self._check_same_dim(other)
            return sum(a * b for a, b in zip(self, other))
        # Vector * scalar → 스칼라 곱
        elif isinstance(other, (int, float)):
            return Vector.of(a * float(other) for a in self)
        else:
            return NotImplemented

    def __rmul__(self, other: Number) -> "Vector":
        # scalar * Vector → 스칼라 곱
        if isinstance(other, (int, float)):
            return Vector.of(float(other) * a for a in self)
        else:
            return NotImplemented

    # --- 수학 유틸 ---
    def norm(self) -> float:
        """유클리드 노름(길이)"""
        return math.sqrt(sum(a * a for a in self))

    def unit(self) -> "Vector":
        """단위 벡터(길이 1). 영벡터는 예외 처리."""
        n = self.norm()
        if n == 0.0:
            raise ZeroDivisionError("영벡터는 단위 벡터를 가질 수 없습니다.")
        return (1.0 / n) * self

    def distance_to(self, other: "Vector") -> float:
        """두 벡터 사이의 유클리드 거리"""
        return (self - other).norm()

    # 파이썬 내장 abs(v)로 노름을 얻을 수 있게 설정
    def __abs__(self) -> float:
        return self.norm()

#Matrix Overloading
@dataclass(frozen=True)
class Matrix:
    """불변 m×n 행렬.
    오버로딩:
      - A + B: 원소별 덧셈
      - A - B: 원소별 뺄셈
      - A * B: 행렬 곱
      - A * v: 행렬-벡터 곱
      - A * k, k * A: 스칼라 곱
    """
    _data: Tuple[Tuple[float, ...], ...]  # 행(row)의 튜플

    # ---- 생성자 ----
    @staticmethod
    def of(rows: Iterable[Iterable[Number]]) -> "Matrix":
        mat = tuple(tuple(float(x) for x in row) for row in rows)
        if not mat or not mat[0]:
            raise ValueError("빈 행렬은 허용하지 않습니다.")
        w = len(mat[0])
        if any(len(r) != w for r in mat):
            raise ValueError("모든 행의 길이가 동일해야 합니다.")
        return Matrix(mat)

    @property
    def shape(self) -> Tuple[int, int]:
        return (len(self._data), len(self._data[0]))

    def __repr__(self) -> str:
        r, c = self.shape
        return f"Matrix({r}×{c})"

    def __str__(self) -> str:
        # 보기 좋은 행렬 출력 (고정 소수 6자리, 공백 정렬)
        rows = []
        for row in self._data:
            cells = [f"{x:.6g}" for x in row]  # 필요하면 자리수 조정
            rows.append("[ " + ", ".join(cells) + " ]")
        return "[\n  " + ",\n  ".join(rows) + "\n]"

    def __getitem__(self, i: int) -> Tuple[float, ...]:
        return self._data[i]

    # ---- 내부 체크 ----
    def _check_same_shape(self, other: "Matrix"):
        if self.shape != other.shape:
            raise ValueError(f"크기 불일치: {self.shape} vs {other.shape}")

    # ---- 전치 ----
    def T(self) -> "Matrix":
        return Matrix.of(zip(*self._data))

    # ---- 덧셈/뺄셈 ----
    def __add__(self, other: "Matrix") -> "Matrix":
        self._check_same_shape(other)
        return Matrix.of(
            (a + b for a, b in zip(row_a, row_b))
            for row_a, row_b in zip(self._data, other._data)
        )

    def __sub__(self, other: "Matrix") -> "Matrix":
        self._check_same_shape(other)
        return Matrix.of(
            (a - b for a, b in zip(row_a, row_b))
            for row_a, row_b in zip(self._data, other._data)
        )

    # ---- 곱셈 오버로딩 ----
    def __mul__(self, other: Union["Matrix", "Vector", Number]) -> Union["Matrix", "Vector"]:
        r, c = self.shape

        # 행렬-행렬 곱
        if isinstance(other, Matrix):
            r2, c2 = other.shape
            if c != r2:
                raise ValueError(f"행렬곱 불가: {self.shape} @ {other.shape}")
            other_T = other.T()  # 열 접근 최적화
            out_rows = []
            for i in range(r):
                row = []
                for j in range(c2):
                    val = sum(self._data[i][k] * other_T._data[j][k] for k in range(c))
                    row.append(val)
                out_rows.append(row)
            return Matrix.of(out_rows)

        # 행렬-벡터 곱
        from typing import cast  # 순환 참조 피하기 위한 지연 import 가독용
        if isinstance(other, Vector):
            if c != len(other):
                raise ValueError(f"행렬-벡터 곱 불가: {self.shape} * {len(other)}D")
            out = [sum(self._data[i][k] * other[k] for k in range(c)) for i in range(r)]
            return Vector.of(out)

        # 스칼라 곱
        if isinstance(other, (int, float)):
            return Matrix.of((x * float(other) for x in row) for row in self._data)

        return NotImplemented

    def __rmul__(self, other: Number) -> "Matrix":
        if isinstance(other, (int, float)):
            return Matrix.of((float(other) * x for x in row) for row in self._data)
        return NotImplemented

    # ---- 단위/영 행렬 ----
    @staticmethod
    def eye(n: int) -> "Matrix":
        return Matrix.of([[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)])

    @staticmethod
    def zeros(r: int, c: int) -> "Matrix":
        return Matrix.of([[0.0 for _ in range(c)] for _ in range(r)])

    # ---- 행렬식 (보고서용 최소 구현: 1~3차) ----
    def det(self) -> float:
        r, c = self.shape
        if r != c:
            raise ValueError("정사각행렬에서만 det를 정의합니다.")
        if r == 1:
            return self._data[0][0]
        if r == 2:
            a, b = self._data[0]
            c2, d = self._data[1]
            return a * d - b * c2
        if r == 3:
            a, b, c3 = self._data[0]
            d, e, f = self._data[1]
            g, h, i = self._data[2]
            return (a*e*i + b*f*g + c3*d*h) - (c3*e*g + b*d*i + a*f*h)
        raise NotImplementedError("det는 1~3차 정사각행렬만 지원합니다.")

