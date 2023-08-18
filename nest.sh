export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
export NEST_PATH="/media/ianpearl/PEARL/Github/casetone/nest_controller/nest_controller"
python /media/ianpearl/PEARL/Github/casetone/nest_controller/nest_controller/sheets.py