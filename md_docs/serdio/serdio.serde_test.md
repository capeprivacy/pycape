<!-- markdownlint-disable -->

<a href="../../serdio/serdio/serde_test.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `serdio.serde_test`






---

<a href="../../serdio/serdio/serde_test.py#L9"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `SerializeTest`







---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L32"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_custom_types`

```python
test_custom_types(x)
```

test_custom_types(x=MyCoolClass(cool_float=2, cool_int=3.0)) 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L32"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_custom_types`

```python
test_custom_types(x)
```

test_custom_types(x=MyCoolResult(cool_result=6.0)) 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L32"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_custom_types`

```python
test_custom_types(x)
```

test_custom_types(x=(MyCoolClass(cool_float=2, cool_int=3.0), MyCoolResult(cool_result=6.0))) 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L32"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_custom_types`

```python
test_custom_types(x)
```

test_custom_types(x={'classes': (MyCoolClass(cool_float=2, cool_int=3.0), MyCoolClass(cool_float=4, cool_int=6.0)), 'results': (MyCoolResult(cool_result=6.0), MyCoolResult(cool_result=24.0))}) 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_serde`

```python
test_serde(x)
```

test_serde(x=b'\xa3foo') 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_serde`

```python
test_serde(x)
```

test_serde(x='foo') 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_serde`

```python
test_serde(x)
```

test_serde(x=b'foo') 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_serde`

```python
test_serde(x)
```

test_serde(x=bytearray(b'\x01')) 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_serde`

```python
test_serde(x)
```

test_serde(x=1) 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_serde`

```python
test_serde(x)
```

test_serde(x=1.0) 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_serde`

```python
test_serde(x)
```

test_serde(x=[1, 2]) 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_serde`

```python
test_serde(x)
```

test_serde(x=(1, 2)) 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_serde`

```python
test_serde(x)
```

test_serde(x={'a': 1, 'b': 2}) 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_serde`

```python
test_serde(x)
```

test_serde(x={1, 2}) 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_serde`

```python
test_serde(x)
```

test_serde(x=frozenset({1, 2})) 

---

<a href="../../venv/lib/python3.9/site-packages/absl/testing/parameterized.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `test_serde`

```python
test_serde(x)
```

test_serde(x=True) 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
