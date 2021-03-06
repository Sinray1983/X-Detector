import tensorflow as tf

USE_FUSED_BN = True
BN_EPSILON = 0.001 #0000000474974513 #0.0010000000474974513
BN_MOMENTUM = 0.99

def reduced_kernel_size_for_small_input(input_tensor, kernel_size):
  shape = input_tensor.get_shape().as_list()
  if shape[1] is None or shape[2] is None:
    kernel_size_out = kernel_size
  else:
    kernel_size_out = [
        min(shape[1], kernel_size[0]), min(shape[2], kernel_size[1])
    ]
  return kernel_size_out

def relu_separable_bn_block(inputs, filters, name_prefix, is_training, data_format):
    bn_axis = -1 if data_format == 'channels_last' else 1

    inputs = tf.nn.relu(inputs, name=name_prefix + '_act')
    inputs = tf.layers.separable_conv2d(inputs, filters, (3, 3),
                        strides=(1, 1), padding='same',
                        data_format=data_format,
                        activation=None, use_bias=False,
                        depthwise_initializer=tf.contrib.layers.xavier_initializer(),
                        pointwise_initializer=tf.contrib.layers.xavier_initializer(),
                        bias_initializer=tf.zeros_initializer(),
                        name=name_prefix, reuse=None)
    inputs = tf.layers.batch_normalization(inputs, momentum=BN_MOMENTUM, name=name_prefix + '_bn', axis=bn_axis,
                            epsilon=BN_EPSILON, training=is_training, reuse=None, fused=USE_FUSED_BN)
    return inputs

def XceptionModel(input_image, num_classes, is_training = False, data_format='channels_last'):
    bn_axis = -1 if data_format == 'channels_last' else 1

    inputs = tf.layers.conv2d(input_image, 32, (3, 3), use_bias=False, name='block1_conv1', strides=(2, 2),
                padding='valid', data_format=data_format, activation=None,
                kernel_initializer=tf.contrib.layers.xavier_initializer(),
                bias_initializer=tf.zeros_initializer())
    inputs = tf.layers.batch_normalization(inputs, momentum=BN_MOMENTUM, name='block1_conv1_bn', axis=bn_axis,
                            epsilon=BN_EPSILON, training=is_training, reuse=None, fused=USE_FUSED_BN)
    inputs = tf.nn.relu(inputs, name='block1_conv1_act')

    inputs = tf.layers.conv2d(inputs, 64, (3, 3), use_bias=False, name='block1_conv2', strides=(1, 1),
                padding='valid', data_format=data_format, activation=None,
                kernel_initializer=tf.contrib.layers.xavier_initializer(),
                bias_initializer=tf.zeros_initializer())
    inputs = tf.layers.batch_normalization(inputs, momentum=BN_MOMENTUM, name='block1_conv2_bn', axis=bn_axis,
                            epsilon=BN_EPSILON, training=is_training, reuse=None, fused=USE_FUSED_BN)
    inputs = tf.nn.relu(inputs, name='block1_conv2_act')


    residual = tf.layers.conv2d(inputs, 128, (1, 1), use_bias=False, name='conv2d_1', strides=(2, 2),
                padding='same', data_format=data_format, activation=None,
                kernel_initializer=tf.contrib.layers.xavier_initializer(),
                bias_initializer=tf.zeros_initializer())
    residual = tf.layers.batch_normalization(residual, momentum=BN_MOMENTUM, name='batch_normalization_1', axis=bn_axis,
                            epsilon=BN_EPSILON, training=is_training, reuse=None, fused=USE_FUSED_BN)


    inputs = tf.layers.separable_conv2d(inputs, 128, (3, 3),
                        strides=(1, 1), padding='same',
                        data_format=data_format,
                        activation=None, use_bias=False,
                        depthwise_initializer=tf.contrib.layers.xavier_initializer(),
                        pointwise_initializer=tf.contrib.layers.xavier_initializer(),
                        bias_initializer=tf.zeros_initializer(),
                        name='block2_sepconv1', reuse=None)
    inputs = tf.layers.batch_normalization(inputs, momentum=BN_MOMENTUM, name='block2_sepconv1_bn', axis=bn_axis,
                            epsilon=BN_EPSILON, training=is_training, reuse=None, fused=USE_FUSED_BN)

    inputs = relu_separable_bn_block(inputs, 128, 'block2_sepconv2', is_training, data_format)

    inputs = tf.layers.max_pooling2d(inputs, pool_size=(3, 3), strides=(2, 2),
                                    padding='same', data_format=data_format,
                                    name='block2_pool')

    inputs = inputs + residual
    residual = tf.layers.conv2d(inputs, 256, (1, 1), use_bias=False, name='conv2d_2', strides=(2, 2),
                padding='same', data_format=data_format, activation=None,
                kernel_initializer=tf.contrib.layers.xavier_initializer(),
                bias_initializer=tf.zeros_initializer())
    residual = tf.layers.batch_normalization(residual, momentum=BN_MOMENTUM, name='batch_normalization_2', axis=bn_axis,
                            epsilon=BN_EPSILON, training=is_training, reuse=None, fused=USE_FUSED_BN)

    inputs = relu_separable_bn_block(inputs, 256, 'block3_sepconv1', is_training, data_format)
    inputs = relu_separable_bn_block(inputs, 256, 'block3_sepconv2', is_training, data_format)

    inputs = tf.layers.max_pooling2d(inputs, pool_size=(3, 3), strides=(2, 2),
                                    padding='same', data_format=data_format,
                                    name='block3_pool')
    inputs = inputs + residual


    residual = tf.layers.conv2d(inputs, 728, (1, 1), use_bias=False, name='conv2d_3', strides=(2, 2),
                padding='same', data_format=data_format, activation=None,
                kernel_initializer=tf.contrib.layers.xavier_initializer(),
                bias_initializer=tf.zeros_initializer())
    residual = tf.layers.batch_normalization(residual, momentum=BN_MOMENTUM, name='batch_normalization_3', axis=bn_axis,
                            epsilon=BN_EPSILON, training=is_training, reuse=None, fused=USE_FUSED_BN)

    inputs = relu_separable_bn_block(inputs, 728, 'block4_sepconv1', is_training, data_format)
    inputs = relu_separable_bn_block(inputs, 728, 'block4_sepconv2', is_training, data_format)

    inputs = tf.layers.max_pooling2d(inputs, pool_size=(3, 3), strides=(2, 2),
                                    padding='same', data_format=data_format,
                                    name='block4_pool')
    inputs = inputs + residual

    for index in range(8):
        residual = inputs
        prefix = 'block' + str(index + 5)

        inputs = relu_separable_bn_block(inputs, 728, prefix + '_sepconv1', is_training, data_format)
        inputs = relu_separable_bn_block(inputs, 728, prefix + '_sepconv2', is_training, data_format)
        inputs = relu_separable_bn_block(inputs, 728, prefix + '_sepconv3', is_training, data_format)

        inputs = inputs + residual


    residual = tf.layers.conv2d(inputs, 1024, (1, 1), use_bias=False, name='conv2d_4', strides=(2, 2),
                padding='same', data_format=data_format, activation=None,
                kernel_initializer=tf.contrib.layers.xavier_initializer(),
                bias_initializer=tf.zeros_initializer())
    residual = tf.layers.batch_normalization(residual, momentum=BN_MOMENTUM, name='batch_normalization_4', axis=bn_axis,
                            epsilon=BN_EPSILON, training=is_training, reuse=None, fused=USE_FUSED_BN)

    inputs = relu_separable_bn_block(inputs, 728, 'block13_sepconv1', is_training, data_format)
    inputs = relu_separable_bn_block(inputs, 1024, 'block13_sepconv2', is_training, data_format)

    inputs = tf.layers.max_pooling2d(inputs, pool_size=(3, 3), strides=(2, 2),
                                    padding='same', data_format=data_format,
                                    name='block13_pool')
    inputs = inputs + residual

    inputs = tf.layers.separable_conv2d(inputs, 1536, (3, 3),
                        strides=(1, 1), padding='same',
                        data_format=data_format,
                        activation=None, use_bias=False,
                        depthwise_initializer=tf.contrib.layers.xavier_initializer(),
                        pointwise_initializer=tf.contrib.layers.xavier_initializer(),
                        bias_initializer=tf.zeros_initializer(),
                        name='block14_sepconv1', reuse=None)
    inputs = tf.layers.batch_normalization(inputs, momentum=BN_MOMENTUM, name='block14_sepconv1_bn', axis=bn_axis,
                            epsilon=BN_EPSILON, training=is_training, reuse=None, fused=USE_FUSED_BN)
    inputs = tf.nn.relu(inputs, name='block14_sepconv1_act')

    inputs = tf.layers.separable_conv2d(inputs, 2048, (3, 3),
                        strides=(1, 1), padding='same',
                        data_format=data_format,
                        activation=None, use_bias=False,
                        depthwise_initializer=tf.contrib.layers.xavier_initializer(),
                        pointwise_initializer=tf.contrib.layers.xavier_initializer(),
                        bias_initializer=tf.zeros_initializer(),
                        name='block14_sepconv2', reuse=None)
    inputs = tf.layers.batch_normalization(inputs, momentum=BN_MOMENTUM, name='block14_sepconv2_bn', axis=bn_axis,
                            epsilon=BN_EPSILON, training=is_training, reuse=None, fused=USE_FUSED_BN)
    inputs = tf.nn.relu(inputs, name='block14_sepconv2_act')

    #inputs1 = inputs
    if data_format == 'channels_first':
        channels_last_inputs = tf.transpose(inputs, [0, 2, 3, 1])
    else:
        channels_last_inputs = inputs

    inputs = tf.layers.average_pooling2d(inputs, pool_size = reduced_kernel_size_for_small_input(channels_last_inputs, [10, 10]), strides = 1, padding='valid', data_format=data_format, name='avg_pool')

    if data_format == 'channels_first':
        inputs = tf.squeeze(inputs, axis=[2, 3])
    else:
        inputs = tf.squeeze(inputs, axis=[1, 2])

    outputs = tf.layers.dense(inputs, num_classes,
                            activation=tf.nn.softmax, use_bias=True,
                            kernel_initializer=tf.contrib.layers.xavier_initializer(),
                            bias_initializer=tf.zeros_initializer(),
                            name='dense', reuse=None)

    return outputs

'''load the IR model with renamed saver, then test the outputs and save with new variable names
'''
# import numpy as np

# name_map = {'beta': 'bias',
#             'gamma': 'scale',
#             'moving_mean': 'mean',
#             'moving_variance': 'var',
#             'kernel':'weight',
#             'depthwise_kernel': 'df',
#             'pointwise_kernel': 'pf'}

# tf.reset_default_graph()

# input_image = tf.placeholder(tf.float32,  shape = (None, 299, 299, 3), name = 'input_placeholder')
# outputs = XceptionModel(input_image, 1000, is_training = False, data_format='channels_last')

# var_to_restore = {}
# for var in tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES):#TRAINABLE_VARIABLES):
#     var_name = var.op.name
#     prefix = var_name[:var_name.rfind('/')]
#     suffix = var_name[var_name.rfind('/') + 1 :]
#     #print(prefix + '_' + name_map[suffix])
#     if 'dense' not in var_name:
#         var_to_restore[prefix + '_' + name_map[suffix]] = var
#     else:
#         var_to_restore[var_name] = var

# saver_restore = tf.train.Saver(var_to_restore)
# saver = tf.train.Saver()

# with tf.Session() as sess:

#     init = tf.global_variables_initializer()
#     sess.run(init)

#     saver_restore.restore(sess, "./model/tf_xception.ckpt")

#     predict = sess.run(outputs, feed_dict = {input_image : np.ones((1,299,299,3)) * 0.5})
#     print(predict)
#     print(np.argmax(predict))

#     save_path = saver.save(sess, "./rename_tf_model/xception_model.ckpt")
#     print("Model saved in path: %s" % save_path)


'''run test for the renamed chcekpoint again
'''
# import numpy as np

# tf.reset_default_graph()

# input_image = tf.placeholder(tf.float32,  shape = (None, 299, 299, 3), name = 'input_placeholder')
# outputs = XceptionModel(input_image, 1000, is_training = False, data_format='channels_last')

# saver = tf.train.Saver()

# with tf.Session() as sess:
#     init = tf.global_variables_initializer()
#     sess.run(init)

#     saver.restore(sess, "./rename_tf_model/xception_model.ckpt")

#     predict = sess.run(outputs, feed_dict = {input_image : np.ones((1,299,299,3)) * 0.5})
#     print(predict)
#     print(np.argmax(predict))


# import numpy as np
# from tensorflow.python.keras._impl.keras.applications.imagenet_utils import decode_predictions  # pylint: disable=unused-import
# import scipy

# tf.reset_default_graph()

# input_image = tf.placeholder(tf.float32,  shape = (None, 299, 299, 3), name = 'input_placeholder')
# outputs = XceptionModel(input_image, 1000, is_training = True, data_format='channels_last')

# saver = tf.train.Saver()

# with tf.Session() as sess:
#     init = tf.global_variables_initializer()
#     sess.run(init)

#     saver.restore(sess, "./rename_tf_model/xception_model.ckpt")

#     image_file = ['images/000013.jpg', 'images/000018.jpg', 'images/000031.jpg', 'images/000038.jpg', 'images/000045.jpg']
#     image_array = []
#     for file in image_file:
#         np_image = scipy.misc.imread(file, mode='RGB')
#         np_image = scipy.misc.imresize(np_image, (299, 299))
#         np_image = np.expand_dims(np_image, axis=0).astype(np.float32)
#         image_array.append(np_image)
#     np_image = np.concatenate(image_array, axis = 0)
#     np_image /= 127.5
#     np_image -= 1.
#     #np_image = np.transpose(np_image, (0, 3, 1, 2))
#     predict = sess.run(outputs, feed_dict = {input_image : np_image})
#     #print(predict)
#     print(np.argmax(predict))
#     print('Predicted:', decode_predictions(predict, 1))


