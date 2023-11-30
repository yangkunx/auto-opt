import shutil, argparse, os, time


parser = argparse.ArgumentParser('trans files', add_help=False)
parser.add_argument("--path", "--p",  type=str, help="the path of source dir")
parser.add_argument("--nightly", "--n", default="ww22.1", type=str, help="tag nightly")
parser.add_argument("--backend", "--b", default="terraform", type=str, help="wsf run backend")


pass_args = parser.parse_args()
path = pass_args.path

dir_name = os.path.basename(path)
    
start_time = time.time()
    
shutil.make_archive(dir_name, 'zip', path)

end_time = time.time()
print("耗时: {:.2f}秒".format(end_time - start_time))