
## 生成发布包
```
pip install --upgrade build
python -m build
```


## 上传到pypi
安装上传工具
```
pip install --upgrade twine
twine upload dist/*
```
