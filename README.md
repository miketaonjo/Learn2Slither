# Learn2Slither

The aim of this project is to introduce the basic concepts behind machine learning. I had to create a program that predicts the price of a car by using a linear function (A linear function predicts a value using a straight line) trained with a gradient descent algorithm (Gradient descent iteratively updates parameters to minimize prediction error).

## Setup
- Python 3.12
- python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

## Lib
- Pandas : Used to load and manipulate the dataset from a CSV file, providing an easy way to access and prepare input data.
- Matplotlib : Used to visualize the dataset and the resulting linear regression line, helping to better understand and debug the model.

## Introduction

First, we need to visualize the datas in order to check if the hypothesis of the model are conceivable before training : Is there a linear relation between all the points ? Are there extreme values ? A reasonable scale for each ?

## Launch
 ```
python train.py
python predict.py