import marimo

__generated_with = "0.14.0"
app = marimo.App(width="full")

with app.setup:
    # Initialization code that runs before all other cells
    import os
    from typing import Optional, Tuple
    import pickle
    import gzip
    from tqdm import tqdm
    import numpy as np
    import matplotlib.pyplot as plt
    from skimage import draw
    from skimage.io import imread, imshow, imread_collection, concatenate_images
    from skimage.transform import resize
    from skimage.morphology import label, binary_erosion, disk
    from skimage.segmentation import find_boundaries
    from joblib import Parallel, delayed

    import sys
    import random
    import warnings
    import pandas as pd
    from itertools import chain
    import tensorflow as tf
    import tensorflow.keras.backend as kb
    import tensorflow.keras.utils as ku
    import tensorflow.keras.callbacks as kc
    from tensorflow.keras.metrics import MeanIoU
    from tensorflow.keras.models import Model, load_model
    from tensorflow.keras.layers import Input
    from tensorflow.keras.layers import Dropout, Lambda
    from tensorflow.keras.layers import Conv2D, Conv2DTranspose
    from tensorflow.keras.layers import MaxPooling2D
    from tensorflow.keras.layers import Lambda
    from tensorflow.keras.layers import concatenate
    from tensorflow.keras.layers import multiply
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.preprocessing import image
    from tensorflow.keras import backend as kb
    from tensorflow.keras import layers as kl


@app.cell
def _(mo):
    mo.md(r"""First, downgrade tensorflow to v2.15. Afterwards, you will have to restart the runtime before continuing with the notebook.""")
    return


@app.cell
def _():
    import subprocess
    subprocess.run(["pip", "install", "tensorflow==2.15"])
    return (subprocess,)


@app.cell
def _():
    ## File paths, change these to the appropriate paths
    train_path = 'train'
    test_path = 'test'
    model_file_name = 'unet_colab_notebook.cfr'

    ## Model training
    mini_batch_size = 1
    epochs = 100
    learning_rate = 0.001
    classifier_type = 'U-Net'
    train_image_size = (0, 0, 1)
    validation_split = 0.1
    erosion_width = 0
    early_stopper = {'active': True, 'kwargs': {'patience': 5}}
    lr_scheduler = {'active': True, 'kwargs': {'patience': 5}}
    model_checkpoint = {'active': True, 'kwargs': {'save_best_only': True}}
    logging = {'active': True, 'kwargs': {}}

    ## Extra parameters
    img_height, img_width, img_channels = train_image_size[0], train_image_size[1], train_image_size[2]
    pickle_protocol = 3
    warnings.filterwarnings('ignore', category=UserWarning, module='skimage')
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    return (
        classifier_type,
        early_stopper,
        epochs,
        erosion_width,
        img_channels,
        img_height,
        img_width,
        learning_rate,
        logging,
        lr_scheduler,
        mini_batch_size,
        model_checkpoint,
        model_file_name,
        pickle_protocol,
        test_path,
        train_path,
        validation_split,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# PyJAMAS notebook for Google Colab""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    Use the following folder structure:

    train/

    	train_folder_name_1/
    		image/
    			train_image_name_1.tif
    		mask/
    			train_image_name_1.tif
    		prev_mask/
    			train_image_name_1.tif

    	.
    	.
    	.

    	train_folder_name_n/
    		image/
    			train_image_name_n.tif
    		mask/
    			train_image_name_n.tif
    		prev_mask/
    			train_image_name_n.tif

    test/

    	test_folder_name_1/
    		image/
    			test_image_name_1.tif
    		mask/
    			test_image_name_1.tif
    		prev_mask/
    			test_image_name_1.tif

    	.
    	.
    	.

    	test_folder_name_m/
    		image/
    			test_image_name_m.tif
    		mask/
    			test_image_name_m.tif
    		prev_mask/
    			test_image_name_m.tif

    Zip up the data into a file (e.g. testtrain.zip) and upload the file into /content in a google colab runtime.
    Then change into the /content folder and unzip the data.
    Alternatively, upload the data to google drive and mount your drive to access the data.
    """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""If you have uploaded the data directly to colab:""")
    return


@app.cell(disabled=True)
def _(subprocess):
    os.chdir("content")
    subprocess.run(["unzip", "testtrain.zip"], shell=True)
    os.chdir("testtrain")
    return


@app.cell
def _(mo):
    mo.md(r"""If you have uploaded the data to google drive:""")
    return


@app.cell(disabled=True)
def _():
    from google.colab import drive
    drive.mount("/content/drive")
    os.chdir("/drive/MyDrive/path/to/testtrain")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Define weight function:""")
    return


@app.function
def weight_map(binmasks, w0=10, sigma=5, show=False):
    """Compute the weight map for a given mask, as described in Ronneberger et al.
    (https://arxiv.org/pdf/1505.04597.pdf)
    """

    labmasks = label(binmasks)
    n_objs = np.amax(labmasks)

    nrows, ncols = labmasks.shape[:2]
    masks = np.zeros((n_objs, nrows, ncols))
    distMap = np.zeros((nrows * ncols, n_objs))
    X1, Y1 = np.meshgrid(np.arange(nrows), np.arange(ncols))
    X1, Y1 = np.c_[X1.ravel(), Y1.ravel()].T
    for i in tqdm(range(n_objs)):
        mask = np.squeeze(labmasks == i + 1)
        bounds = find_boundaries(mask, mode='inner')
        X2, Y2 = np.nonzero(bounds)
        xSum = (X2.reshape(-1, 1) - X1.reshape(1, -1)) ** 2
        ySum = (Y2.reshape(-1, 1) - Y1.reshape(1, -1)) ** 2
        distMap[:, i] = np.sqrt(xSum + ySum).min(axis=0)
        masks[i] = mask
    ix = np.arange(distMap.shape[0])
    if distMap.shape[1] == 1:
        d1 = distMap.ravel()
        border_loss_map = w0 * np.exp((-1 * (d1) ** 2) / (2 * (sigma ** 2)))
    else:
        if distMap.shape[1] == 2:
            d1_ix, d2_ix = np.argpartition(distMap, 1, axis=1)[:, :2].T
        else:
            d1_ix, d2_ix = np.argpartition(distMap, 2, axis=1)[:, :2].T
        d1 = distMap[ix, d1_ix]
        d2 = distMap[ix, d2_ix]
        border_loss_map = w0 * np.exp((-1 * (d1 + d2) ** 2) / (2 * (sigma ** 2)))
    xBLoss = np.zeros((nrows, ncols))
    xBLoss[X1, Y1] = border_loss_map
    # class weight map
    loss = np.zeros((nrows, ncols))
    w_1 = 1 - masks.sum() / loss.size
    w_0 = 1 - w_1
    loss[masks.sum(0) == 1] = w_1
    loss[masks.sum(0) == 0] = w_0
    ZZ = xBLoss + loss
    # ZZ = resize(ZZ, outsize, preserve_range=True)
    if show:
        plt.imshow(ZZ)
        plt.colorbar()
        plt.axis('off')
    return ZZ


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Resize images and normalize intensities:""")
    return


@app.function
def process_training_data(folder: str, height: int, width: int, channels: int, scaler: float = None):
    ids = next(os.walk(folder))[1]

    # Get and resize train images and masks
    X = np.zeros((len(ids), height, width, channels), dtype=np.uint16)
    Y = np.zeros((len(ids), height, width, 1), dtype=bool)
    W = np.zeros((len(ids), height, width, 1), dtype=float)
    print('Getting and resizing train images and masks ... ')

    for n, id_ in enumerate(ids):
        path = os.path.join(folder, id_)
        im_file = os.path.join(path, "image", os.listdir(os.path.join(path, "image"))[0])
        img = imread(im_file)
        if img.ndim == 3:
            img = img[0, :, :]
        img = np.expand_dims(resize(img, (height, width), order=3,
                                          mode='constant', preserve_range=True), axis=-1)
        X[n] = img
        msk_file = os.path.join(path, "mask", os.listdir(os.path.join(path, "mask"))[0])
        mask = np.zeros((height, width, 1), dtype=bool)
        mask_ = imread(msk_file)
        mask_ = np.expand_dims(resize(mask_, (height, width), order=0,
                                            mode='constant', preserve_range=True), axis=-1)
        mask = np.maximum(mask, mask_)
        weights = weight_map(mask)
        Y[n] = mask
        W[n, :, :, 0] = weights

    if scaler is None:
        scaler = np.amax(X)
    X = X / scaler

    wmap = np.zeros((X.shape[0], height, width, 2), dtype=np.float32)
    wmap[..., 0] = W.squeeze()
    wmap[..., 1] = W.squeeze()
    W = wmap

    Y = ku.to_categorical(Y)
    return X, Y, W, scaler


@app.cell
def _(img_channels, img_height, img_width, test_path, train_path):
    X_train, Y_train, W_train, scaler = process_training_data(train_path, img_height, img_width, img_channels)
    X_test, Y_test, W_test, _ = process_training_data(test_path, img_height, img_width, img_channels, scaler)

    _epsilon = tf.convert_to_tensor(kb.epsilon(), np.float32)
    return W_train, X_test, X_train, Y_test, Y_train, scaler


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Define loss function:""")
    return


@app.function
def pixelwise_loss(target, output):
    """
    A custom function defined to simply sum the pixelwise loss.
    This function doesn't compute the crossentropy loss, since that is made a
    part of the model's computational graph itself.
    Parameters
    ----------
    target : tf.tensor
        A tensor corresponding to the true labels of an image.
    output : tf.tensor
        Model output
    Returns
    -------
    tf.tensor
        A tensor holding the aggregated loss.
    """
    return - tf.reduce_sum(target * output,
                           len(output.get_shape()) - 1)


@app.cell
def _(mo):
    mo.md(r"""Define the network:""")
    return


@app.function
def make_weighted_loss_unet(input_shape, n_classes):
    # two inputs, one for the image and one for the weight maps
    ip = tf.keras.Input(shape=input_shape, name="image_input")
    # the shape of the weight maps has to be such that it can be element-wise
    # multiplied to the softmax output.
    weight_ip = tf.keras.Input(shape=input_shape[:2] + (n_classes,))

    # adding the layers
    conv1 = kl.Conv2D(64, 3, activation='relu', padding='same', kernel_initializer='he_normal')(ip)
    conv1 = kl.Conv2D(64, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv1)
    conv1 = kl.Dropout(0.1)(conv1)
    mpool1 = kl.MaxPool2D()(conv1)

    conv2 = kl.Conv2D(128, 3, activation='relu', padding='same', kernel_initializer='he_normal')(mpool1)
    conv2 = kl.Conv2D(128, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv2)
    conv2 = kl.Dropout(0.2)(conv2)
    mpool2 = kl.MaxPool2D()(conv2)

    conv3 = kl.Conv2D(256, 3, activation='relu', padding='same', kernel_initializer='he_normal')(mpool2)
    conv3 = kl.Conv2D(256, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv3)
    conv3 = kl.Dropout(0.3)(conv3)
    mpool3 = kl.MaxPool2D()(conv3)

    conv4 = kl.Conv2D(512, 3, activation='relu', padding='same', kernel_initializer='he_normal')(mpool3)
    conv4 = kl.Conv2D(512, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv4)
    conv4 = kl.Dropout(0.4)(conv4)
    mpool4 = kl.MaxPool2D()(conv4)

    conv5 = kl.Conv2D(1024, 3, activation='relu', padding='same', kernel_initializer='he_normal')(mpool4)
    conv5 = kl.Conv2D(1024, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv5)
    conv5 = kl.Dropout(0.5)(conv5)

    up6 = kl.Conv2DTranspose(512, 2, strides=2, kernel_initializer='he_normal', padding='same')(conv5)
    conv6 = kl.Concatenate()([up6, conv4])
    conv6 = kl.Conv2D(512, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv6)
    conv6 = kl.Conv2D(512, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv6)
    conv6 = kl.Dropout(0.4)(conv6)

    up7 = kl.Conv2DTranspose(256, 2, strides=2, kernel_initializer='he_normal', padding='same')(conv6)
    conv7 = kl.Concatenate()([up7, conv3])
    conv7 = kl.Conv2D(256, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv7)
    conv7 = kl.Conv2D(256, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv7)
    conv7 = kl.Dropout(0.3)(conv7)

    up8 = kl.Conv2DTranspose(128, 2, strides=2, kernel_initializer='he_normal', padding='same')(conv7)
    conv8 = kl.Concatenate()([up8, conv2])
    conv8 = kl.Conv2D(128, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv8)
    conv8 = kl.Conv2D(128, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv8)
    conv8 = kl.Dropout(0.2)(conv8)

    up9 = kl.Conv2DTranspose(64, 2, strides=2, kernel_initializer='he_normal', padding='same')(conv8)
    conv9 = kl.Concatenate()([up9, conv1])
    conv9 = kl.Conv2D(64, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv9)
    conv9 = kl.Conv2D(64, 3, activation='relu', padding='same', kernel_initializer='he_normal')(conv9)
    conv9 = kl.Dropout(0.1)(conv9)

    c10 = kl.Conv2D(n_classes, 1, activation='softmax', kernel_initializer='he_normal', name="unet-activation")(conv9)

    # Add a few non trainable layers to mimic the computation of the crossentropy
    # loss, so that the actual loss function just has to peform the
    # aggregation.
    c11 = kl.Lambda(lambda x: x / tf.reduce_sum(x, len(x.get_shape()) - 1, True))(c10)
    c11 = kl.Lambda(lambda x: tf.clip_by_value(x, _epsilon, 1. - _epsilon))(c11)
    c11 = kl.Lambda(lambda x: kb.log(x))(c11)
    weighted_sm = kl.multiply([c11, weight_ip])

    model = Model(inputs=[ip, weight_ip], outputs=[weighted_sm])
    return model


@app.cell
def _(mo):
    mo.md(r"""Define a function that will add the enabled callbacks to the training loop:""")
    return


@app.function
def build_callbacks(early_stopper, lr_scheduler, model_checkpoint, logging, validation_split: float = 0.0):
    callbacks = []
    if early_stopper['active']:
        if validation_split > 0:
            monitor = 'val_loss'
        else:
            raise Warning("Using early stopping without a validation split is not recommended. "
                          "Setting early stopping to monitor train loss.")
            monitor = 'train_loss'
        callbacks.append(kc.EarlyStopping(monitor, restore_best_weights=True, **early_stopper['kwargs']))
    if lr_scheduler['active']:
        callbacks.append(kc.ReduceLROnPlateau(monitor='val_loss' if validation_split > 0 else 'train_loss',
                                              **lr_scheduler['kwargs']))
    if model_checkpoint['active']:
        if model_checkpoint['kwargs']['save_best_only']:
            fname = "ckpt_best.weights.h5"
        else:
            fname = "ckpt_epoch{epoch:02d}.weights.h5"

        callbacks.append(kc.ModelCheckpoint(os.path.join(os.getcwd(), fname), monitor='val_loss' if validation_split > 0 else 'train_loss', save_weights_only=True,
                                      **model_checkpoint['kwargs']))
    if logging['active']:
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        callbacks.append(kc.TensorBoard(log_dir, **logging['kwargs']))

    return callbacks


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Create and train the network:""")
    return


@app.cell(disabled=True)
def _(
    W_train,
    X_train,
    Y_train,
    early_stopper,
    epochs,
    img_channels,
    img_height,
    img_width,
    learning_rate,
    logging,
    lr_scheduler,
    mini_batch_size,
    model_checkpoint,
    validation_split,
):
    model = make_weighted_loss_unet((img_height, img_width, img_channels), 2)
    callbacks = build_callbacks(early_stopper, lr_scheduler, model_checkpoint, logging, validation_split)

    adam = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(adam, loss=pixelwise_loss)

    history = model.fit([X_train, W_train], Y_train, batch_size=mini_batch_size, epochs=epochs, validation_split=validation_split, callbacks=callbacks)
    return history, model


@app.cell
def _(mo):
    mo.md(r"""If the best checkpoint was saved, load the weights from that checkpoint:""")
    return


@app.cell
def _(model, model_checkpoint):
    if model_checkpoint['active'] and model_checkpoint['kwargs']['save_best_only']:
        model.load_weights("ckpt_best.weights.h5")
    return


@app.cell
def _(mo):
    mo.md(r"""Plot the training and validation loss:""")
    return


@app.cell
def _(history, validation_split):
    plt.plot(history.history['loss'])
    if validation_split > 0:
        plt.plot(history.history['val_loss'])
        plt.legend(['loss', 'val_loss'])
    plt.gca()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Save and download the model (can be loaded into PyJAMAS):""")
    return


@app.cell
def _(
    classifier_type,
    early_stopper,
    epochs,
    erosion_width,
    img_channels,
    img_height,
    img_width,
    learning_rate,
    logging,
    lr_scheduler,
    mini_batch_size,
    model,
    model_checkpoint,
    model_file_name,
    pickle_protocol,
    scaler,
    train_path,
):
    from google.colab import files
    theclassifier = {

        'classifier_type': classifier_type,
        'positive_training_folder': train_path,
        'train_image_size': (img_height, img_width, img_channels),
        'scaler': scaler,
        'epochs': epochs,
        'mini_batch_size': mini_batch_size,
        'learning_rate': learning_rate,
        'step_sz': (img_height, img_width),
        'erosion_width': erosion_width,
        'classifier': model.get_weights(),
        'early_stopper': early_stopper, 
        'lr_scheduler': lr_scheduler, 
        'model_checkpoint': model_checkpoint, 
        'logging': logging,
    }

    try:
        fh = gzip.open(os.path.join('/content', model_file_name), "wb")
        pickle.dump(theclassifier, fh, pickle_protocol)

    except (IOError, OSError) as ex:
        if fh is not None:
            fh.close()

    fh.close()

    files.download(os.path.join('/content', model_file_name))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Grab output layers for testing here in the notebook:""")
    return


@app.cell
def _(model):
    image_input = model.get_layer('image_input').input
    softmax_output = model.get_layer('unet-activation').output
    predictor = kb.function([image_input], [softmax_output])
    return (predictor,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Sample test for the first image in the test set (set ind=i for the (i+1)th image):""")
    return


@app.cell
def _(
    X_test,
    Y_test,
    erosion_width,
    img_channels,
    img_height,
    img_width,
    predictor,
):
    ind = 0
    testImage = X_test[ind]
    yhat = predictor([testImage.reshape((1, img_height, img_width, img_channels))])[0]
    yhat = np.argmax(yhat[0], axis=-1)
    testLabel = Y_test[ind][:, :, 1]

    if erosion_width > 0:
        testLabel = binary_erosion(testLabel, disk(erosion_width))

    fig, (ax1, ax2, ax3) = plt.subplots(nrows=1, ncols=3, figsize=(50, 300))
    ax1.imshow(np.squeeze(testImage), cmap=plt.cm.gray)
    ax1.set_title("image")
    ax2.imshow(np.squeeze(yhat), cmap=plt.cm.gray)
    ax2.set_title("ground truth mask")
    ax3.imshow(np.squeeze(testLabel), cmap=plt.cm.gray)
    ax3.set_title("output mask")
    return


@app.cell
def _():
    # This cell is needed to create the notebook, but does not need to be run in colab
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
