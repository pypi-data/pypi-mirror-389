# colocal  

**Colab or local — same behaviour, same results.**  

`colocal` is a lightweight utility that harmonises notebook environments across **Google Colab** and **local Jupyter**.  

It takes care of paths, imports, and working directories automatically, so your notebooks behave consistently no matter where you run them.   

---

## ✨ Features  

- **Seamless dual support** → Detects whether you’re in Colab or Jupyter and adjusts automatically.  
- **Clean imports** → Adds your repository root to `sys.path`.  
- **Consistent working directory** → Sets `cwd` to the notebook’s folder, avoiding `../../` hacks.  
- **Branch-aware in Colab** → Parses the Colab badge, checks out the correct branch, and mirrors the repo structure.  
- **Reproducibility** → Run the same notebook in Colab or locally with identical behaviour.  

---

## 🚀 Usage  

```python
import colocal
colocal.setup()
```
