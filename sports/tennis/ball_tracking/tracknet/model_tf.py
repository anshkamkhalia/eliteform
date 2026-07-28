import tensorflow as tf

def build_tracknet():

    input = tf.keras.Input(shape=(360, 640, 9))

    # layer 1 (initial feature extraction)
    x = tf.keras.layers.Conv2D(64, (3,3), padding='same', kernel_initializer='random_uniform',)(input)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 2 (initial feature extraction)
    x = tf.keras.layers.Conv2D(64, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 3 (downsample)
    x = tf.keras.layers.MaxPool2D((2,2), strides=(2,2))(x)

    # layer 4 (feature extraction)
    x = tf.keras.layers.Conv2D(128, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 5 (feature extraction)
    x = tf.keras.layers.Conv2D(128, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 6 (downsample)
    x = tf.keras.layers.MaxPool2D((2,2), strides=(2,2))(x)

    # layer 7 (feature extraction)
    x = tf.keras.layers.Conv2D(256, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 8 (feature extraction)
    x = tf.keras.layers.Conv2D(256, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 9 (feature extraction)
    x = tf.keras.layers.Conv2D(256, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 10 (downsample)
    x = tf.keras.layers.MaxPool2D((2,2), strides=(2,2))(x)

    # layer 11 (feature extraction)
    x = tf.keras.layers.Conv2D(512, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 12 (feature extraction)
    x = tf.keras.layers.Conv2D(512, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 13 (feature extraction)
    x = tf.keras.layers.Conv2D(512, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 14 (upsample)
    x = tf.keras.layers.UpSampling2D((2,2))(x)

    # layer 15 (feature extraction)
    x = tf.keras.layers.Conv2D(256, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 16 (feature extraction)
    x = tf.keras.layers.Conv2D(256, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 17 (feature extraction)
    x = tf.keras.layers.Conv2D(256, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 18 (upsample)
    x = tf.keras.layers.UpSampling2D((2,2))(x)

    # layer 19 (feature extraction)
    x = tf.keras.layers.Conv2D(128, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 20 (feature extraction)
    x = tf.keras.layers.Conv2D(128, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 21 (upsample)
    x = tf.keras.layers.UpSampling2D((2,2))(x)

    # layer 22 (feature extraction)
    x = tf.keras.layers.Conv2D(64, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 23 (feature extraction)
    x = tf.keras.layers.Conv2D(64, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # layer 23 (feature extraction)
    x = tf.keras.layers.Conv2D(256, (3,3), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # output heatmap
    x = tf.keras.layers.Conv2D(1, (1,1), padding='same', kernel_initializer='random_uniform',)(x)
    x = tf.keras.layers.Activation('sigmoid')(x)

    model = tf.keras.Model(inputs=input, outputs=x)

    return model