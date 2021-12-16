docker build -t binance-image .
docker run --network host -it --rm --name binance-run binance-image
