import tensorflow as tf
import cv2
import datetime
import time
import argparse
import os

import posenet


parser = argparse.ArgumentParser()
parser.add_argument('--model', type=int, default=101)
parser.add_argument('--scale_factor', type=float, default=1.0)
parser.add_argument('--notxt', action='store_true')
parser.add_argument('--video', type=str, required=True)
args = parser.parse_args()


def main():

    with tf.Session() as sess:
        model_cfg, model_outputs = posenet.load_model(args.model, sess)
        output_stride = model_cfg['output_stride']

        video = cv2.VideoCapture(args.video)
        formatted_date = datetime.datetime.now().strftime("%Y%m%d-%H%M")
        path = '/opt/cv/result/pose-results/posenet/' + formatted_date + '-' + str(args.model)
        i = 0

        if not os.path.exists(path):
            os.makedirs(path)

        start = time.time()

        while True:
            input_image, draw_image, output_scale = posenet.read_cap(
                video, scale_factor=args.scale_factor, output_stride=output_stride)

            if input_image is None:
                break

            heatmaps_result, offsets_result, displacement_fwd_result, displacement_bwd_result = sess.run(
                model_outputs,
                feed_dict={'image:0': input_image}
            )

            pose_scores, keypoint_scores, keypoint_coords = posenet.decode_multiple_poses(
                heatmaps_result.squeeze(axis=0),
                offsets_result.squeeze(axis=0),
                displacement_fwd_result.squeeze(axis=0),
                displacement_bwd_result.squeeze(axis=0),
                output_stride=output_stride,
                max_pose_detections=10,
                min_pose_score=0.25)

            keypoint_coords *= output_scale

            draw_image = posenet.draw_skel_and_kp(
                draw_image, pose_scores, keypoint_scores, keypoint_coords,
                min_pose_score=0.25, min_part_score=0.25)

            cv2.imwrite(path + '/' + str(i) + '.jpg', draw_image)

            if not args.notxt:
                print()
                print("Results for image: %i" % i)
                for pi in range(len(pose_scores)):
                    if pose_scores[pi] == 0.:
                        break
                    print('Pose #%d, score = %f' % (pi, pose_scores[pi]))
                    for ki, (s, c) in enumerate(zip(keypoint_scores[pi, :], keypoint_coords[pi, :, :])):
                        print('Keypoint %s, score = %f, coord = %s' % (posenet.PART_NAMES[ki], s, c))

            i += 1

        print('Average FPS:', i / (time.time() - start))


if __name__ == "__main__":
    main()