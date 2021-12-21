sudo docker build -t binance-image .
sudo docker run --network host -it --rm --name binance-run binance-image
