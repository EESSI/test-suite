import os

import tensorflow as tf
import numpy as np

# Should go in the EESSI MIXin class and than also at a check for a path set to all the files needed
if os.environ.get('EESSI_TEST_SUITE_NO_DOWNLOAD') == 'True':
    eessi_test_suite_download=False
else:
    eessi_test_suite_download=True

def mnist_dataset(batch_size, test_batch_size):
    if eessi_test_suite_download:
        (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
    else:
        if "EESSI_TEST_SUITE_DOWNLOAD_DIR" in os.environ:
            download_path = os.environ['EESSI_TEST_SUITE_DOWNLOAD_DIR']
            mnist_path = os.path.join(download_path, 'datasets', 'mnist.npz')
            if os.path.exists(mnist_path):
                with  np.load(mnist_path, allow_pickle=True) as data:
                    x_train, y_train = data['x_train'], data['y_train']
                    x_test, y_test = data['x_test'], data['y_test']
            else:
                raise ValueError(f'could not find {mnist_path} and cannot download.')
        else:
            raise ValueError('The TensorFlow test requires EESSI_TEST_SUITE_DOWNLOAD_DIR to be set if not allowed to download the dataset.')
    if eessi_test_suite_download:
        (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
    else:
        if os.environ['KERAS_HOME']:
            print(os.environ['KERAS_HOME'])
        else:
            raise ValueError('The TensorFlow test requires KERAS_HOME to be set if not allowed to download the dataset')
    # The `x` arrays are in uint8 and have values in the [0, 255] range.
    # You need to convert them to float32 with values in the [0, 1] range.
    x_train = x_train / np.float32(255)
    y_train = y_train.astype(np.int64)
    x_test = x_test / np.float32(255)
    y_test = y_test.astype(np.int64)
    train_dataset = tf.data.Dataset.from_tensor_slices(
        (x_train, y_train)).shuffle(60000).repeat().batch(batch_size)
    test_dataset = tf.data.Dataset.from_tensor_slices(
        (x_test, y_test)).batch(test_batch_size)
    return train_dataset, test_dataset


def build_and_compile_cnn_model():
    model = tf.keras.Sequential([
        tf.keras.layers.InputLayer(input_shape=(28, 28)),
        tf.keras.layers.Reshape(target_shape=(28, 28, 1)),
        tf.keras.layers.Conv2D(32, 3, activation='relu'),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(10)
    ])
    model.compile(
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        metrics=['accuracy'])
    return model
