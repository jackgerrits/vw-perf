import os
import time
import subprocess
import json
import textwrap

import util
import find
import clone
import statistics

import sys

from tabulate import tabulate

from typing import Callable, Tuple, List, Union, TextIO, Optional, Any, Dict


def make_command_line_test(
        vw_bin: str, command_line: str, cwd=None) -> Tuple[Callable[[], None], str]:
    def command_line_test():
        util.check_result_throw(
            subprocess.run((vw_bin + " " + command_line).split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, cwd=cwd))

    return command_line_test, command_line


def gen_steps(cache_dir):
    def get_steps(vw_bin: str) -> List[Tuple[Callable[[], None], str]]:
        """Add functions here that will run as part of the harness. They should return the time in
        seconds it took to run it.
        """
        runtests_data_dir = os.path.join(cache_dir, "data/runtests_data/")
        return [
            make_command_line_test(vw_bin, "-k -l 20 --initial_t 128000 --power_t 1 -d train-sets/0001.dat -f models/0001_1.model -c --passes 8 --invariant --ngram 3 --skips 1 --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -t -d train-sets/0001.dat -i models/0001_1.model -p 0001.predict --invariant", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/0002.dat -f models/0002.model --invariant", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/0002.dat -f models/0002.model --invariant", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k --initial_t 1 --adaptive --invariant -q Tf -q ff -f models/0002a.model -d train-sets/0002.dat", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -t -i models/0002.model -d train-sets/0002.dat -p 0002b.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k --power_t 0.45 -f models/0002c.model -d train-sets/0002.dat", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -t -i models/0002c.model -d train-sets/0002.dat -p 0002c.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/cs_test.ldf -p cs_test.ldf.csoaa.predict --passes 10 --invariant --csoaa_ldf multiline --holdout_off --noconstant", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/cs_test.ldf -p cs_test.ldf.wap.predict --passes 10 --invariant --wap_ldf multiline --holdout_off --noconstant", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k --oaa 10 -c --passes 10 -d train-sets/multiclass --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k --ect 10 --error 3 -c --passes 10 --invariant -d train-sets/multiclass --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/wsj_small.dat.gz --passes 6 --search_task sequence --search 45 --search_alpha 1e-6 --search_max_bias_ngram_length 2 --search_max_quad_ngram_length 1 --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/wsj_small.dat.gz --passes 6 --search_task sequence --search 45 --search_alpha 1e-6 --search_max_bias_ngram_length 2 --search_max_quad_ngram_length 1 --holdout_off --search_passes_per_policy 3 --search_interpolation policy", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/zero.dat --loss_function=squared -b 20 --bfgs --mem 7 --passes 5 --l2 1.0 --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/rcv1_small.dat --loss_function=logistic --bfgs --mem 7 --passes 20 --termination 0.001 --l2 1.0 --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k --lda 100 --lda_alpha 0.01 --lda_rho 0.01 --lda_D 1000 -l 1 -b 13 --minibatch 128 -d train-sets/wiki256.dat", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/seq_small --passes 12 --invariant --search 4 --search_task sequence --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/3parity --hash all --passes 3000 -b 16 --nn 2 -l 10 --invariant -f models/0021.model --random_seed 19 --quiet --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/3parity -t -i models/0021.model -p 0022.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -f models/xxor.model -d train-sets/xxor.dat --cubic abc --passes 100 --holdout_off --progress 1.33333", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/ml100k_small_train -b 16 -q ui --rank 10 --l2 2e-6 --learning_rate 0.05 --passes 2 --decay_learning_rate 0.97 --power_t 0 -f models/movielens.reg -c --loss_function classic --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-i models/movielens.reg -t -d test-sets/ml100k_small_test", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k --active --simulation --mellowness 0.000001 -d train-sets/rcv1_small.dat -l 10 --initial_t 10 --random_seed 3", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/0002.dat -f models/bs.reg.model --bootstrap 4 -p bs.reg.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/0002.dat -i models/bs.reg.model -p bs.prreg.predict -t", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/0001.dat -f models/bs.vote.model --bootstrap 4 --bs_type vote -p bs.vote.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/0001.dat -i models/bs.vote.model -p bs.prvote.predict -t", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/affix_test.dat -k -c --passes 10 --holdout_off --affix -2", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/0001.dat -f models/mask.model --invert_hash mask.predict --l1 0.01", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/0001.dat --invert_hash remask.predict --feature_mask models/mask.model -f models/remask.model", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/0001.dat --feature_mask models/mask.model -i models/remask.model", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/topk.vw -f topk.model -q MF --passes 100 --cache_file topk-train.cache -k --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-P 1 -d train-sets/topk.vw -i topk.model --top 2 -p topk-rec.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k --passes 100 -c --holdout_off --constant 1000 -d train-sets/big-constant.dat", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/0001.dat --progress 10", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/0001.dat -P 0.5", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/0001.dat --nn 1", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/rcv1_raw_cb_small.vw --cb 2 --cb_type dr --ngram 2 --skips 4 -b 24 -l 0.25", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/rcv1_raw_cb_small.vw --cb 2 --cb_type ips --ngram 2 --skips 4 -b 24 -l 0.125", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/rcv1_raw_cb_small.vw --cb 2 --cb_type dm --ngram 2 --skips 4 -b 24 -l 0.125 -f cb_dm.reg", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/lda-2pass-hang.dat --lda 10 -c --passes 2 --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/sequence_data --passes 20 --invariant --search_rollout ref --search_alpha 1e-8 --search_task sequence --search 5 --holdout_off -f models/sequence_data.model", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/sequence_data -t -i models/sequence_data.model -p sequence_data.nonldf.test.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/seq_small2 --passes 4 --search 4 --search_task sequence --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/sequence_data --passes 20 --search_rollout ref --search_alpha 1e-8 --search_task sequence_demoldf --csoaa_ldf m --search 5 --holdout_off -f models/sequence_data.ldf.model --noconstant", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/sequence_data -t -i models/sequence_data.ldf.model -p sequence_data.ldf.test.predict --noconstant", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/sequencespan_data --passes 20 --invariant --search_rollout none --search_task sequencespan --search 7 --holdout_off -f models/sequencespan_data.model", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/sequencespan_data -t -i models/sequencespan_data.model -p sequencespan_data.nonldf.test.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/sequencespan_data --passes 20 --invariant --search_rollout ref --search_alpha 1e-8 --search_task sequencespan --search_span_bilou --search 7 --holdout_off VW} -d train-sets/sequencespan_data -t --search_span_bilou -i models/sequencespan_data.model -p sequencespan_data.nonldf-bilou.test.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/argmax_data -k -c --passes 20 --search_rollout ref --search_alpha 1e-8 --search_task argmax --search 2 --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c --passes 2 -d train-sets/0001.dat", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--stage_poly --sched_exponent 0.25 --batch_sz 1000 --batch_sz_no_doubling -d train-sets/rcv1_small.dat -p stage_poly.s025.predict --quiet", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--stage_poly --sched_exponent 1.0 --batch_sz 1000 --batch_sz_no_doubling -d train-sets/rcv1_small.dat --quiet", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--stage_poly --sched_exponent 0.25 --batch_sz 1000 -d train-sets/rcv1_small.dat -p stage_poly.s025.doubling.predict --quiet", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--stage_poly --sched_exponent 1.0 --batch_sz 1000 -d train-sets/rcv1_small.dat -p stage_poly.s100.doubling.predict --quiet", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-c -k -d train-sets/library_train -f models/library_train.w -q st --passes 100 --hash all --noconstant --csoaa_ldf m --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, " --dsjson --cb_adf -d train-sets/no_shared_features.json", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--ksvm --l2 1 --reprocess 5 -b 18 -p ksvm_train.linear.predict -d train-sets/rcv1_smaller.dat", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--ksvm --l2 1 --reprocess 5 -b 18 --kernel poly -p ksvm_train.poly.predict -d train-sets/rcv1_smaller.dat", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--ksvm --l2 1 --reprocess 5 -b 18 --kernel rbf -p ksvm_train.rbf.predict -d train-sets/rcv1_smaller.dat", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/er_small.vw --passes 6 --search_task entity_relation --search 10 --constraints --search_alpha 1e-8", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/wsj_small.dparser.vw.gz --passes 6 --search_task dep_parser --search 12  --search_alpha 1e-4 --search_rollout oracle --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/dictionary_test.dat --binary --ignore w --holdout_off --passes 32 --dictionary w:dictionary_test.dict --dictionary w:dictionary_test.dict.gz --dictionary_path train-sets", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/multiclass.sch --passes 20 --search_task multiclasstask --search 10 --search_alpha 1e-4 --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/sequence_data -t -i models/sequence_data.model -p sequence_data.nonldf.beam.test.predict --search_metatask selective_branching --search_max_branch 10 --search_kbest 10", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/sequence_data -t -i models/sequence_data.ldf.model -p sequence_data.ldf.beam.test.predict --search_metatask selective_branching --search_max_branch 10 --search_kbest 10 --noconstant", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/0002.dat --autolink 1 --examples 100 -p 0002.autolink.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/0001.dat -f models/0001_ftrl.model --passes 1 --ftrl --ftrl_alpha 0.01 --ftrl_beta 0 --l1 2", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -t -d train-sets/0001.dat -i models/0001_ftrl.model -p 0001_ftrl.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/rcv1_cb_eval --cb 2 --eval", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--log_multi 10 -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cbify 10 --epsilon 0.05 -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cbify 10 --first 5 -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cbify 10 --bag 7 -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cbify 10 --cover 3 -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--lrq aa3 -d train-sets/0080.dat", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/0001.dat -f models/ftrl_pistol.model --passes 1 --pistol", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -t -d train-sets/0001.dat -i models/ftrl_pistol.model -p ftrl_pistol.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/0080.dat --redefine := --redefine y:=: --redefine x:=arma --ignore x -q yy", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_adf -d train-sets/cb_test.ldf --noconstant", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--multilabel_oaa 10 -d train-sets/multilabel -p multilabel.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--csoaa_ldf multiline --csoaa_rank -d train-sets/cs_test_multilabel.ldf -p multilabel_ldf.predict --noconstant", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_adf --rank_all -d train-sets/cb_test.ldf -p cb_adf_rank.predict --noconstant", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--named_labels det,noun,verb --oaa 3 -d train-sets/test_named  -k -c --passes 10 --holdout_off -f models/test_named.model", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-i models/test_named.model -t -d train-sets/test_named -p test_named.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--named_labels det,noun,verb --csoaa 3 -d train-sets/test_named_csoaa  -k -c --passes 10 --holdout_off -f models/test_named_csoaa.model", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-i models/test_named_csoaa.model -t -d train-sets/test_named_csoaa -p test_named_csoaa.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -l 20 --initial_t 128000 --power_t 1 -d train-sets/0001.dat -c --passes 8 --invariant --ngram 3 --skips 1 --holdout_off --replay_b 100", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--named_labels det,noun,verb --csoaa 3 -d train-sets/test_named_csoaa -k -c --passes 10 --holdout_off -f models/test_named_csoaa.model --replay_c 100", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/0001.dat -f models/0097.model --save_resume", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--preserve_performance_counters -d train-sets/0001.dat -i models/0097.model -p 0098.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/0001.dat -i models/0097.model -p 0099.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/sequence_data --passes 20 --invariant --search_rollout none --search_task sequence_ctg --search 5 --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--loss_function logistic --binary --active_cover -d train-sets/rcv1_mini.dat -f models/active_cover.model", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-i models/active_cover.model -t -d test-sets/rcv1_small_test.data -p active_cover.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--loss_function logistic --binary --active_cover --oracular -d ./train-sets/rcv1_small.dat", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_adf -d train-sets/cb_test.ldf --cb_type mtr --noconstant", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/0001.dat -f models/0001_ftrl.model --passes 10 --ftrl --ftrl_alpha 3.0 --ftrl_beta 0 --l1 0.9 --cache", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -t -d train-sets/0001.dat -i models/0001_ftrl.model -p 0001_ftrl_holdout.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/0001.dat -f models/0001_ftrl.model --passes 10 --ftrl --ftrl_alpha 0.01 --ftrl_beta 0 --l1 2 --cache --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -t -d train-sets/0001.dat -i models/0001_ftrl.model -p 0001_ftrl_holdout_off.predict --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/probabilities.dat --probabilities --oaa=4 --loss_function=logistic -p oaa_probabilities.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/cs_test.ldf --probabilities --csoaa_ldf=mc --loss_function=logistic -p csoaa_ldf_probabilities.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/wsj_small.dparser.vw.gz -b 20 --search_task dep_parser --search 25 --search_alpha 1e-5 --search_rollin mix_per_roll --search_rollout oracle --one_learner --nn 5 --ftrl --search_history_length 3 --root_label 8", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/wsj_small.dparser.vw.gz -b 20 --passes 6 --search_task dep_parser --search 25 --search_alpha 1e-5 --search_rollin mix_per_roll --search_rollout none --holdout_off --search_history_length 3 --root_label 8 --cost_to_go", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--confidence -d ./train-sets/rcv1_micro.dat --initial_t 0.1 -p confidence.preds", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/x.txt", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/long_line -c -k", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/cb_eval --multiworld_test f -p cb_eval.preds", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/0001.dat -i models/0001_ftrl.model  --audit_regressor ftrl.audit_regr", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/test_named_csoaa -i models/test_named_csoaa.model --audit_regressor csoaa.audit_regr", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/cb_eval --multiworld_test f --learn 2 -p mwt_learn.preds", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/cb_eval --multiworld_test f --learn 2 --exclude_eval -p mwt_learn_exclude.preds", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/rcv1_raw_cb_small.vw --cb_explore 2 --ngram 2 --skips 4 -b 24 -l 0.25 -p rcv1_raw_cb_explore.preds", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--confidence --confidence_after_training --initial_t 0.1 -d ./train-sets/rcv1_small.dat -p confidence_after_training.preds", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/cb_eval1 --multiworld_test f -f mwt.model -p cb_eval1.preds", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/cb_eval2 -i mwt.model -p cb_eval2.preds", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -c -d train-sets/wsj_small.dparser.vw.gz -b 20 --search_task dep_parser --search 26 --search_alpha 1e-5 --search_rollin mix_per_roll --search_rollout oracle --one_learner --search_history_length 3 --root_label 8 --transition_system 2 --passes 8", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--quiet -d train-sets/gauss1k.dat.gz -f models/recall_tree_g100.model --recall_tree 100 -b 20 --loss_function logistic", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-t -d train-sets/gauss1k.dat.gz -i models/recall_tree_g100.model", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_explore_adf --epsilon 0.1 -d train-sets/cb_test.ldf --noconstant -p cbe_adf_epsilon.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_explore_adf --softmax --lambda 1 -d train-sets/cb_test.ldf --noconstant -p cbe_adf_softmax.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_explore_adf --bag 3 -d train-sets/cb_test.ldf --noconstant -p cbe_adf_bag.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_explore_adf --first 2 -d train-sets/cb_test.ldf --noconstant -p cbe_adf_first.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--quiet -d train-sets/poisson.dat -f models/poisson.model --loss_function poisson --link poisson -b 2 -p poisson.train.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--quiet -d train-sets/poisson.dat -f models/poisson.normalized.model --normalized --loss_function poisson --link poisson -b 2 -l 0.1 -p poisson.train.normalized.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--OjaNewton -d train-sets/0001.dat -f models/second_order.model -p second_order.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/cb_adf_crash_1.data -f models/cb_adf_crash.model --cb_explore_adf --epsilon 0.05", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/cb_adf_crash_2.data -i models/cb_adf_crash.model -t", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--audit -d train-sets/audit.dat --noconstant", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_explore_adf --cover 3 -d train-sets/cb_test.ldf --noconstant -p cbe_adf_cover.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_explore_adf --cover 3 --cb_type dr -d train-sets/cb_test.ldf --noconstant -p cbe_adf_cover_dr.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--marginal f  -d train-sets/marginal_features --noconstant --initial_numerator 0.5 --initial_denominator 1.0 --decay 0.001 --holdout_off -c -k --passes 100 -f marginal_model", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-i marginal_model  -d train-sets/marginal_features --noconstant -t", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--explore_eval --epsilon 0.2 -d train-sets/cb_test.ldf --noconstant -p explore_eval.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -l 20 --initial_t 128000 --power_t 1 -d train-sets/0001.json --json -c --passes 8 --invariant --ngram 3 --skips 1 --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_explore_adf --cover 3 --cb_type dr -d train-sets/cb_test.json --json --noconstant -p cbe_adf_cover_dr.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--bootstrap 2 -d train-sets/labeled-unlabeled-mix.dat", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_explore_adf --cover 3 --cb_type dr -d train-sets/cb_test256.json --json --noconstant -p cbe_adf_cover_dr256.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/probabilities.dat --scores --oaa=4 -p oaa_scores.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_adf -d train-sets/cb_test.ldf -p cb_adf_dm.predict --cb_type dm", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_adf -d train-sets/cb_test.ldf -p cb_adf_dm.predict --cb_type dm --sparse_weights", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--lrqfa aa3 -d train-sets/0080.dat", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--marginal f  -d train-sets/marginal_features --noconstant --initial_numerator 0.5 --initial_denominator 1.0 --decay 0.001 --holdout_off -c -k --passes 100  --compete", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k --cache_file ignore_linear.cache --passes 10000 --holdout_off -d train-sets/0154.dat --noconstant --ignore_linear x -q xx", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/0001.dat -i models/0097.model --save_resume --audit_regressor 0097.audit_regr", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/0001.dat -f models/sr.model  --passes 2 -c -k  -P 50 --save_resume", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/decisionservice.json --dsjson --cb_explore_adf --epsilon 0.2 --quadratic GT -P 1 -p cbe_adf_dsjson.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/rcv1_mini.dat --bootstrap 5 --binary -c -k --passes 2", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/multiclass --bootstrap 4 --oaa 10 -q :: --leave_duplicate_interactions  -c -k --passes 2 --holdout_off -P1", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/0001.dat --classweight 1:2,0:3.1,-1:5", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--oaa 10 -d train-sets/multiclass --classweight 4:0,7:0.1,2:10 --classweight 10:3", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--recall_tree 10 -d train-sets/multiclass --classweight 4:0,7:0.1 --classweight 2:10,10:3", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cs_active 3 -d ../test/train-sets/cs_test --cost_max 2 --mellowness 0.01 --simulation --adax", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cs_active 3 -d ../test/train-sets/cs_test --cost_max 2 --mellowness 1.0 --simulation --adax", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--hash_seed 5 -d train-sets/rcv1_mini.dat --holdout_off --passes 2 -f hash_seed5.model -c -k --ngram 2 -q ::", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/rcv1_mini.dat -i hash_seed5.model -t", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/rcv1_raw_cb_small.vw -t -i cb_dm.reg", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/rcv1_multiclass.dat --cbify 2 --epsilon 0.05", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cbify 10 --cb_explore_adf --epsilon 0.05 -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cbify 3 --cbify_cs --epsilon 0.05 -d train-sets/cs_cb", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cbify 3 --cbify_cs --cb_explore_adf --epsilon 0.05 -d train-sets/cs_cb", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cbify 10 --cb_explore_adf --cb_type mtr --regcb --mellowness 0.01 -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cbify 10 --cb_explore_adf --cb_type mtr --regcbopt --mellowness 0.01 -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/cs_test.ldf --cbify_ldf --cb_type mtr --regcbopt --mellowness 0.01", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, " --dsjson --cb_adf -d train-sets/no_shared_features.json", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--warm_cb 10 --cb_explore_adf --cb_type mtr --epsilon 0.05 --warm_start 3 --interaction 7 --choices_lambda 8 --warm_start_update --interaction_update -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--warm_cb 10 --cb_explore_adf --cb_type mtr --epsilon 0.05 --warm_start 3 --interaction 7 --choices_lambda 8 --lambda_scheme 2 --warm_start_update --interaction_update -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--warm_cb 10 --cb_explore_adf --cb_type mtr --epsilon 0.05 --warm_start 3 --interaction 7 --choices_lambda 8 --interaction_update -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--warm_cb 10 --cb_explore_adf --cb_type mtr --epsilon 0.0 --warm_start 3 --interaction 7 --choices_lambda 8 --warm_start_update -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--warm_cb 10 --cb_explore_adf --cb_type mtr --epsilon 0.05 --warm_start 3 --interaction 7 --choices_lambda 1 --warm_start_update --interaction_update --sim_bandit -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--warm_cb 10 --cb_explore_adf --cb_type mtr --epsilon 0.05 --warm_start 3 --interaction 7 --choices_lambda 8 --warm_start_update --interaction_update --corrupt_type_warm_start 2 --corrupt_prob_warm_start 0.5 -d train-sets/multiclass", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--warm_cb 3 --cb_explore_adf --cb_type mtr --epsilon 0.05 --warm_start 1 --interaction 2 --choices_lambda 8 --warm_start_update --interaction_update --warm_cb_cs -d train-sets/cs_cb", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -P 100 --holdout_after 500 -d train-sets/0002.dat", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -P 100 --holdout_after 500 -d train-sets/0002.dat -c --passes 2", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_adf --rank_all -d train-sets/cb_adf_sm.data -p cb_adf_sm.predict --cb_type sm", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/b1848_dsjson_parser_regression.txt --dsjson --cb_explore_adf -P 1", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k --oaa 10 --oaa_subsample 5 -c --passes 10 -d train-sets/multiclass --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -d train-sets/0001.dat -f models/ftrl_coin.model --passes 1 --coin", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-k -t -d train-sets/0001.dat -i models/ftrl_coin.model -p ftrl_coin.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/malformed.dat --onethread", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/rcv1_smaller.dat --memory_tree 10 --learn_at_leaf --max_number_of_labels 2 --dream_at_update 0 --dream_repeats 3 --online --leaf_example_multiplier 10 --alpha 0.1 -l 0.001 -b 15 --passes 1 --loss_function squared --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/rcv1_smaller.dat --memory_tree 10 --learn_at_leaf --max_number_of_labels 2 --dream_at_update 0 --dream_repeats 3 --leaf_example_multiplier 10 --alpha 0.1 -l 0.001 -b 15 -c --passes 2 --loss_function squared --holdout_off", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_sample --cb_explore_adf -d test-sets/cb_sample_seed.data -p cb_sample_seed.predict --random_seed 1234", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "-d train-sets/ccb_test.dat --ccb_explore_adf -p ccb_test.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--cb_explore_adf --softmax --lambda 100000 -d train-sets/cb_test.ldf --noconstant -p cbe_adf_softmax_biglambda.predict", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--ccb_explore_adf --ring_size 7 -d train-sets/ccb_reuse_small.data", cwd=runtests_data_dir),
            make_command_line_test(vw_bin, "--ccb_explore_adf --ring_size 20 --dsjson -d train-sets/ccb_reuse_medium.dsjson", cwd=runtests_data_dir)
            # make_command_line_test(vw_bin, "--no_stdin"),
            # make_command_line_test(
            #     vw_bin, f"-d {cache_dir}/data/rcv1/rcv1/rcv1.train.vw.gz -f r_temp"),
            # This specific test must run after the previous test as it uses the produced model.
            # make_command_line_test(vw_bin, f"-d {cache_dir}/data/rcv1/rcv1/rcv1.test.vw.gz -t -i r_temp"),
            # make_command_line_test(
            #     vw_bin,
            #     f"-t --dsjson -d {cache_dir}/data/cb_data/cb_data.dsjson --cb_explore_adf --ignore XA -q UB "
            #     "--epsilon 0.2 -l 0.5 --cb_type mtr --power_t 0"),
            # make_command_line_test(
            #     vw_bin,
            #     f"--dsjson -d {cache_dir}/data/cb_data/cb_data.dsjson --cb_explore_adf --ignore XA -q UB "
            #     "--epsilon 0.2 -l 0.5 --cb_type mtr --power_t 0"),
        ]
    return get_steps


def run_harness(vw_bin: str,
                num_runs: int,
                step_generator: Callable[[str], List[Tuple[Callable[[], None],
                                                           str]]], quiet=False):
    benchmarks = []
    steps = step_generator(vw_bin)
    for step, name in steps:
        if not quiet:
            print(f"Running bench: '{name}'", end ="")

        runs = []
        # Average over number of runs
        for i in range(num_runs):
            if not quiet:
                print(f"\rRunning bench: '{name}', run {i}/{num_runs}",end ="")
            start_time = time.perf_counter()
            # Run the step
            try:
                step()
            except util.CommandFailed as e:
                print()
                print(e)
                print(e.stderr)
                print(e.stdout)
                raise

            end_time = time.perf_counter()
            runs.append(end_time - start_time)
        benchmarks.append({"vw_bin": vw_bin, "name": name, "runs": runs})
        if not quiet:
            print(f"\rRunning bench: '{name}', run {num_runs}/{num_runs} - Done")
    return benchmarks


class PerfInfo:
    def __init__(self, json_data=Optional[Dict[str, Any]]):
        if json_data is not None:
            self.perf_data = json_data
        else:
            self.perf_data = {}

    @staticmethod
    def from_file(file_name):
        with open('data.json') as f:
            return PerfInfo(json.load(f))

    @staticmethod
    def from_string(json_string):
        return PerfInfo(json.loads(json_string))

    def ref_exists(self, commit_ref: str) -> bool:
        return commit_ref in self.perf_data

    def set_ref_info(self, commit_ref: str, author, title, date):
        if not self.ref_exists(commit_ref):
            self.perf_data[commit_ref] = {}

        self.perf_data[commit_ref]["author"] = author
        self.perf_data[commit_ref]["title"] = title
        self.perf_data[commit_ref]["date"] = date

    def remove_ref(self, commit_ref):
        self.perf_data.pop(commit_ref, None)

    def add_benchmark_data(self, commit_ref, benchmark_name, runs):
        if "benchmarks" not in self.perf_data[commit_ref]:
            self.perf_data[commit_ref]["benchmarks"] = {}

        if benchmark_name not in self.perf_data[commit_ref]["benchmarks"]:
            self.perf_data[commit_ref]["benchmarks"][benchmark_name] = {}

        if "runs" not in self.perf_data[commit_ref]["benchmarks"][
                benchmark_name]:
            self.perf_data[commit_ref]["benchmarks"][benchmark_name][
                "runs"] = []

        self.perf_data[commit_ref]["benchmarks"][benchmark_name][
            "name"] = benchmark_name
        self.perf_data[commit_ref]["benchmarks"][benchmark_name][
            "runs"].extend(runs)
        self.perf_data[commit_ref]["benchmarks"][benchmark_name][
            "average"] = sum(self.perf_data[commit_ref]["benchmarks"]
                             [benchmark_name]["runs"]) / len(
                                 self.perf_data[commit_ref]["benchmarks"]
                                 [benchmark_name]["runs"])

    def save_to_file(self, file_name: str):
        with open(file_name, 'w') as f:
            json.dump(self.perf_data, f)


def run(commits, num, from_ref, to_ref, num_runs, skip_existing, cache_dir):
    COMMITS_REPOS_DIR = os.path.join(cache_dir,"./clones/")
    BIN_NAME = "vw"
    commits_to_process = clone.resolve_args_to_commit_list(
        cache_dir, commits, num, from_ref, to_ref)

    commits_and_bins = []
    for commit in commits_to_process:
        commit_path = os.path.realpath(os.path.join(COMMITS_REPOS_DIR, commit))
        if not os.path.exists(commit_path):
            print(
                "{commit} does not exist. Please checkout and build using `python3 run.py clone "
                f"--commits {commit}`")
        vw_bins = find.find_all(BIN_NAME, commit_path)
        commits_and_bins.append((commit, vw_bins[0]))

    if os.path.exists('data.json'):
        perf_info = PerfInfo.from_file('data.json')
    else:
        perf_info = PerfInfo()

    for ref, vw_bin in commits_and_bins:
        print(f"Testing {ref}")

        try:
            if perf_info.ref_exists(ref) and skip_existing == True:
                print(f"Skipping {ref} found - skipping")
                continue

            # Run harness
            benchmarks = run_harness(os.path.realpath(vw_bin), num_runs,
                                     gen_steps(cache_dir))

            # Save commit info
            info = clone.get_commit_info(cache_dir, ref)
            perf_info.set_ref_info(ref, info["author"], info["title"],
                                   info["date"])

            # Record benchmark info
            for bnch in benchmarks:
                perf_info.add_benchmark_data(ref, bnch["name"], bnch["runs"])

            # Save as we go in case of quit/crash
            perf_info.save_to_file("data.json")

        except util.CommandFailed as e:
            perf_info.remove_ref(ref)
            print(f"Skipping {ref}, failed with: {e}")
            continue
    perf_info.save_to_file("data.json")

def run_for_binary(vw_bin_to_test, reference_binary, num_runs, cache_dir):
    """If binary is None, search for it"""

    # TODO: support if reference_binary is None

    DATA_DIR = os.path.join(cache_dir, "./data/")
    if not os.path.exists(DATA_DIR):
        print("Data directory not found - run: `python .\\run.py prepare`")
        sys.exit(1)

    ref_info = None
    try:
        ref_info = clone.get_commit_info(cache_dir, clone.get_current_commit(cache_dir))
    except util.CommandFailed:
        print("Warning: Commit info could not be found. Are you inside the vowpal_wabbit git repo?")

    print(f"Running test benchmarks on '{vw_bin_to_test}'...")
    test_benchmarks = run_harness(os.path.realpath(vw_bin_to_test), num_runs, gen_steps(cache_dir), quiet=False)
    print(f"Running reference benchmarks on '{reference_binary}'...")
    reference_benchmarks = run_harness(os.path.realpath(reference_binary), num_runs, gen_steps(cache_dir), quiet=False)

    if ref_info:
        print(ref_info)
    else:
        print("No commit info available")

    # TODO support extended statistics
    table = []
    for test_bench, reference_bench in zip(test_benchmarks, reference_benchmarks):
        test_mean = statistics.mean(test_bench["runs"])
        # test_median = statistics.median(test_bench["runs"])
        # test_stdev = statistics.pstdev(test_bench["runs"])
        reference_mean = statistics.mean(reference_bench["runs"])
        # reference_median = statistics.median(reference_bench["runs"])
        # reference_stdev = statistics.pstdev(reference_bench["runs"])
        table.append([test_bench["name"], num_runs, test_mean, reference_mean, test_mean - reference_mean, (test_mean - reference_mean) / reference_mean*100])

    formatted_table = tabulate(table, headers=["name", "number of runs", "test mean (s)", "reference mean (s)", "difference (s)", "difference (%)"])
    print(formatted_table)

    tsv_formatted_table = tabulate(table, headers=["name", "number of runs", "test mean (s)", "reference mean (s)", "difference (s)", "difference (%)"], tablefmt="tsv")
    with open("results.tsv","w") as text_file:
        text_file.write(tsv_formatted_table)

