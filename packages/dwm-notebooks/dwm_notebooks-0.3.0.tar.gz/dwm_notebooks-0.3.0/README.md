# dwm-notebooks

This package bundles six machine-learning/notebook examples and provides a small CLI to extract them to an easy-to-access folder on your system.

Install:

  pip install dwm-notebooks

Usage (after installing):

  dwm-install             # copies notebooks to ~/dwm_notebooks
  dwm-install --dest DIR  # copy to an explicit directory

Gemini terminal chat (updated in 0.3.0):

- Run `dwm-gemini` to open an interactive terminal session that helps craft code snippets.
  - The assistant is locked to the `gemini-2.5-flash` model.
  - Use `--system-instruction` to customize the code assistant persona.
  - The CLI is pre-configured with a Gemini API key, so no extra setup is required.

The package includes the following notebooks:

- apriori.ipynb
- clustering.ipynb
- Kmean.ipynb
- naive_bayes.ipynb
- text_mining.ipynb
- pagerank.ipynb
