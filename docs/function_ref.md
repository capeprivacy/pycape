<!-- markdownlint-disable -->

<a href="../pycape/function_ref.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `function_ref`
A structured representation of a deployed Cape function. 

A FunctionRef is intended to capture any/all metadata related to a Cape function. It is generally created from user-supplied metadata, which is given to the user as output of the Cape CLI's `deploy` command. 

Usage: 

 fid = "asdf231lkg1324afdg"  fhash = str(b"2l1h21jhgb2k1jh3".hex())  fref = FunctionRef(fid, fhash) 

 cape = Cape()  cape.connect(fref) 

 fref2 = FunctionRef(fid)  fref2.set_hash(fhash) 

 assert fref == fref2 



---

<a href="../pycape/function_ref.py#L23"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `FunctionRef`
A structured reference to a Cape function. 

<a href="../pycape/function_ref.py#L26"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(function_id, function_hash=None)
```

Instantiate a FunctionRef. 



**Args:**
 
 - <b>`function_id`</b>:  Required string denoting the function ID of the deployed Cape  function. This is typically given in the output of the Cape CLI's  `deploy` command. 
 - <b>`function_hash`</b>:  Optional string denoting the function hash of the deployed  Cape function. If supplied, the Cape client will attempt to verify that  enclave responses include a matching function hash whenever this  FunctionRef is included in Cape requests. 




---

<a href="../pycape/function_ref.py#L46"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_hash`

```python
get_hash()
```





---

<a href="../pycape/function_ref.py#L43"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_id`

```python
get_id()
```





---

<a href="../pycape/function_ref.py#L49"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `set_hash`

```python
set_hash(function_hash)
```








---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
