
import pathlib
import pytz
import os
import time

from datetime import datetime
from flask import Flask, flash, redirect, render_template, \
        request, session, url_for, send_from_directory, make_response

from common.config import globals
from web import app, utils
from web.actions import chia, plotman, chiadog, worker, log_handler, stats

@app.route('/')
def landing():
    gc = globals.load()
    if not globals.is_setup():
        return redirect(url_for('setup'))
    return render_template('landing.html')

@app.route('/index')
def index():
    gc = globals.load()
    if not globals.is_setup():
        return redirect(url_for('setup'))
    if not utils.is_controller():
        return redirect(url_for('controller'))
    workers = worker.load_worker_summary()
    farming = chia.load_farm_summary()
    plotting = plotman.load_plotting_summary()
    challenges = chia.recent_challenges()
    partials = chia.load_partials()
    daily_diff = stats.load_daily_diff()
    return render_template('index.html', reload_seconds=60, farming=farming.__dict__, \
        plotting=plotting.__dict__, challenges=challenges, workers=workers, 
        daily_diff=daily_diff, partials=partials, global_config=gc)

@app.route('/views/challenges')
def views_challenges():
    challenges = chia.recent_challenges()
    return render_template('views/challenges.html', challenges=challenges)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if globals.is_setup():
        return redirect(url_for('index'))
    key_paths = globals.get_key_paths()
    app.logger.debug("Setup found these key paths: {0}".format(key_paths))
    show_setup = True
    if request.method == 'POST':
        if request.form.get('action') == 'generate':
            show_setup = not chia.generate_key(key_paths[0])
        elif request.form.get('action') == 'import':
            show_setup = not chia.import_key(key_paths[0], request.form.get('mnemonic'))
    if show_setup:
        return render_template('setup.html', key_paths = key_paths)
    else:
        return redirect(url_for('index'))

@app.route('/controller')
def controller():
    return render_template('controller.html', controller_url = utils.get_controller_web())

@app.route('/plotting', methods=['GET', 'POST'])
def plotting():
    gc = globals.load()
    if request.method == 'POST':
        if request.form.get('action') == 'start':
            hostname= request.form.get('hostname')
            plotter = worker.get_worker_by_hostname(hostname)
            if request.form.get('service') == 'plotting':
                plotman.start_plotman(plotter)
            elif request.form.get('service') == 'archiving':
                plotman.start_archiving(plotter)
        elif request.form.get('action') == 'stop':
            hostname= request.form.get('hostname')
            plotter = worker.get_worker_by_hostname(hostname)
            if request.form.get('service') == 'plotting':
                plotman.stop_plotman(plotter)
            elif request.form.get('service') == 'archiving':
                plotman.stop_archiving(plotter)
        elif request.form.get('action') in ['suspend', 'resume', 'kill']:
            action = request.form.get('action')
            plot_ids = request.form.getlist('plot_id')
            plotman.action_plots(action, plot_ids)
        else:
            app.logger.info("Unknown plotting form: {0}".format(request.form))
        return redirect(url_for('plotting')) # Force a redirect to allow time to update status
    plotters = plotman.load_plotters()
    plotting = plotman.load_plotting_summary()
    return render_template('plotting.html', reload_seconds=60,  plotting=plotting, 
        plotters=plotters, global_config=gc)

@app.route('/farming')
def farming():
    if request.args.get('analyze'):  # Xhr with a plot filename
        plot_file = request.args.get('analyze')
        plotters = worker.load_worker_summary().plotters
        return plotman.analyze(plot_file, plotters)
    elif request.args.get('check'):  # Xhr calling for check output
        w = worker.get_worker_by_hostname(request.args.get('hostname'))
        first_load = request.args.get("first_load")
        return chia.check_plots(w, first_load)
    gc = globals.load()
    farmers = chia.load_farmers()
    farming = chia.load_farm_summary()
    plots = chia.load_plots_farming()
    daily_notifications = stats.load_daily_notifications()
    return render_template('farming.html', farming=farming, plots=plots, 
        farmers=farmers, daily_notifications=daily_notifications, global_config=gc)

@app.route('/plots_check')
def plots_check():
    return render_template('plots_check.html')

@app.route('/alerts', methods=['GET', 'POST'])
def alerts():
    gc = globals.load()
    if request.method == 'POST':
        if request.form.get('action') == 'start':
            w = worker.get_worker_by_hostname(request.form.get('hostname'))
            chiadog.start_chiadog(w)
        elif request.form.get('action') == 'stop':
            w = worker.get_worker_by_hostname(request.form.get('hostname'))
            chiadog.stop_chiadog(w)
        elif request.form.get('action') == 'remove':
            chiadog.remove_alerts(request.form.getlist('unique_id'))
        else:
            app.logger.info("Unknown alerts form: {0}".format(request.form))
        return redirect(url_for('alerts')) # Force a redirect to allow time to update status
    farmers = chiadog.load_farmers()
    notifications = chiadog.get_notifications()
    return render_template('alerts.html', reload_seconds=60, farmers=farmers,
        notifications=notifications, global_config=gc)

@app.route('/wallet')    
def wallet():
    gc = globals.load()
    wallets = chia.load_wallets()
    return render_template('wallet.html', wallets=wallets, 
        global_config=gc)

@app.route('/keys')
def keys():
    gc = globals.load()
    keys = chia.load_keys_show()
    key_paths = globals.get_key_paths()
    return render_template('keys.html', keys=keys, 
        key_paths=key_paths, global_config=gc)

@app.route('/workers', methods=['GET', 'POST'])
def workers():
    gc = globals.load()
    if request.method == 'POST':
        if request.form.get('action') == "prune":
            worker.prune_workers_status(request.form.getlist('hostname'))
    workers = worker.load_worker_summary()
    return render_template('workers.html', reload_seconds=60, 
        workers=workers, global_config=gc, now=gc['now'])

@app.route('/network/blockchain')
def network_blockchain():
    gc = globals.load()
    blockchains = chia.load_blockchain_show()
    return render_template('network/blockchain.html', reload_seconds=60, 
        blockchains=blockchains, global_config=gc, now=gc['now'])

@app.route('/network/connections', methods=['GET', 'POST'])
def network_connections():
    gc = globals.load()
    if request.method == 'POST':
        if request.form.get('action') == "add":
            chia.add_connection(request.form.get("connection"))
        else:
            app.logger.info("Unknown form action: {0}".format(request.form))
    connections = chia.load_connections_show()
    return render_template('network/connections.html', reload_seconds=60, 
        connections=connections, global_config=gc, now=gc['now'])

def find_selected_worker(workers_summary, hostname):
    if len(workers_summary.workers) == 0:
        return None
    for worker in workers_summary.workers:
        if worker.hostname == hostname:
            return worker
    return workers_summary.workers[0]

@app.route('/settings/plotting', methods=['GET', 'POST'])
def settings_plotting():
    selected_worker_hostname = None
    gc = globals.load()
    if request.method == 'POST':
        selected_worker_hostname = request.form.get('worker')
        plotman.save_config(worker.get_worker_by_hostname(selected_worker_hostname), request.form.get("config"))
    workers_summary = worker.load_worker_summary()
    selected_worker = find_selected_worker(workers_summary, selected_worker_hostname)
    return render_template('settings/plotting.html',
        workers=workers_summary.plotters, selected_worker=selected_worker, global_config=gc)

@app.route('/settings/farming', methods=['GET', 'POST'])
def settings_farming():
    selected_worker_hostname = None
    blockchains = os.environ['blockchains'].split(',')
    selected_blockchain = blockchains[0]
    gc = globals.load()
    if request.method == 'POST':
        selected_worker_hostname = request.form.get('worker')
        selected_blockchain = request.form.get('blockchain')
        chia.save_config(worker.get_worker_by_hostname(selected_worker_hostname), selected_blockchain, request.form.get("config"))
    workers_summary = worker.load_worker_summary()
    selected_worker = find_selected_worker(workers_summary, selected_worker_hostname)
    return render_template('settings/farming.html', blockchains=blockchains, selected_blockchain=selected_blockchain,
        workers=workers_summary.farmers_harvesters, selected_worker=selected_worker, global_config=gc)

@app.route('/settings/alerts', methods=['GET', 'POST'])
def settings_alerts():
    selected_worker_hostname = None
    blockchains = os.environ['blockchains'].split(',')
    selected_blockchain = blockchains[0]
    gc = globals.load()
    if request.method == 'POST':
        selected_worker_hostname = request.form.get('worker')
        selected_blockchain = request.form.get('blockchain')
        chiadog.save_config(worker.get_worker_by_hostname(selected_worker_hostname), selected_blockchain, request.form.get("config"))
    workers_summary = worker.load_worker_summary()
    selected_worker = find_selected_worker(workers_summary, selected_worker_hostname)
    return render_template('settings/alerts.html', blockchains=blockchains, selected_blockchain=selected_blockchain,
        workers=workers_summary.farmers_harvesters, selected_worker=selected_worker, global_config=gc)

@app.route('/settings/pools', methods=['GET', 'POST'])
def settings_pools():
    gc = globals.load()
    if request.method == 'POST':
        plotnfts = chia.load_plotnfts()
        current_pool_url = plotnfts.get_current_pool_url()
        chia.process_pool_save(request.form.get('choice'), request.form.get('pool_url'), current_pool_url)
    plotnfts = chia.load_plotnfts()
    plotnft_log = chia.get_plotnft_log()
    current_pool_url = plotnfts.get_current_pool_url()
    return render_template('settings/pools.html', plotnfts=plotnfts, current_pool_url=current_pool_url, 
        plotnft_log = plotnft_log, global_config=gc)

@app.route('/settings/config', defaults={'path': ''})
@app.route('/settings/config/<path:path>')
def views_settings_config(path):
    w = worker.get_worker_by_hostname(request.args.get('worker'))
    config_type = request.args.get('type')
    if config_type == "alerts":
        response = make_response(chiadog.load_config(w, request.args.get('blockchain')), 200)
    elif config_type == "farming":
        response = make_response(chia.load_config(w, request.args.get('blockchain')), 200)
    elif config_type == "plotting":
        [replaced, config] = plotman.load_config(w)
        response = make_response(config, 200)
        response.headers.set('ConfigReplacementsOccurred', replaced)
    else:
        abort("Unsupported config type: {0}".format(config_type), 400)
    response.mimetype = "application/x-yaml"
    return response

@app.route('/logs')
def logs():
    return render_template('logs.html')

@app.route('/logfile')
def logfile():
    w = worker.get_worker_by_hostname(request.args.get('hostname'))
    log_type = request.args.get("log")
    if log_type in [ 'alerts', 'farming', 'plotting', 'archiving']:
        log_id = request.args.get("log_id")
        blockchain = request.args.get("blockchain")
        return log_handler.get_log_lines(w, log_type, log_id, blockchain)
    else:
        abort(500, "Unsupported log type: {0}".format(log_type))

@app.route('/worker_launch')
def worker_launch():
    [farmer_pk, pool_pk, pool_contract_address] = plotman.load_plotting_keys()
    pathlib.Path('/root/.chia/machinaris/tmp/').mkdir(parents=True, exist_ok=True)
    pathlib.Path('/root/.chia/machinaris/tmp/worker_launch.tmp').touch()
    return render_template('worker_launch.html', farmer_pk=farmer_pk, 
        pool_pk=pool_pk, pool_contract_address=pool_contract_address)

@app.route('/pools')
def pools():
    gc = globals.load()
    pools = chia.load_pools()
    return render_template('pools.html', pools=pools, global_config=gc)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
            'favicon.ico', mimetype='image/vnd.microsoft.icon')