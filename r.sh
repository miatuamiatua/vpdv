rm -r __pycache__
cd app
rm -r __pycache__
cd auth
rm -r __pycache__
cd ..
cd errors
rm -r __pycache__
cd ..
cd main
rm -r __pycache__
cd ../..
cd app
cd avatars
optipng *.png
cd ..
cd static/banners
optipng *.png
cd ../../..
export FLASK_APP=vpdv.py
gunicorn -b 0.0.0.0:5000 -w 10 vpdv:app