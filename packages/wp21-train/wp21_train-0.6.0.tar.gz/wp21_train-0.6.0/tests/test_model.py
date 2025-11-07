from torch import nn
import tensorflow as tf

def keras_mlp():
    inputs  = tf.keras.Input(shape=(784,), name="pixels")
    x       = tf.keras.layers.Dense(128, activation="relu", name="hidden")(inputs)
    logits  = tf.keras.layers.Dense(10 , name="logits")(x)
    outputs = tf.keras.layers.Activation("softmax", name="softmax")(logits)
    return tf.keras.Model(inputs, outputs, name="mnist_float")

class TorchMLP(nn.Module):
    def __init__(self, in_dim=784, hidden=128, out_dim=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, out_dim),
        )

    def forward(self, x):
        return self.net(x)

def torch_mlp(**kwargs):
    return TorchMLP(**kwargs)
