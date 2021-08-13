# Initialize the scheduler only once, not in each worker
def on_starting(server):
    import atexit
    import os
    import time

    from apscheduler.schedulers.background import BackgroundScheduler

    from api import app
    from api.schedules import status_worker, status_farm, status_plotting, \
        status_plots, status_challenges, status_wallets, status_blockchains, \
        status_connections, status_keys, status_alerts, status_controller, \
        status_plotnfts, status_points, status_pools, status_partials
    from api.schedules import stats_disk, stats_farm

    scheduler = BackgroundScheduler()

    # Statistics gathering locally
    scheduler.add_job(func=stats_farm.collect, name="stats_farm", trigger='cron', minute=0)  # Hourly
    scheduler.add_job(func=stats_disk.collect, name="stats_disk", trigger='cron', minute="*/5") # Every 5 minutes

    # Testing only
    #scheduler.add_job(func=stats_farm.collect, trigger='interval', seconds=10) # Test immediately
    #scheduler.add_job(func=stats_disk.collect, trigger='interval', seconds=10) # Test immediately

    # Status gathering - reported via API
    scheduler.add_job(func=status_challenges.update, name="challenges", trigger='interval', seconds=5)
    scheduler.add_job(func=status_worker.update, name="workers", trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_controller.update, name="controller", trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_farm.update, name="farms", trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_plotting.update, name="plottings", trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_plots.update, name="plots", trigger='interval', seconds=60, jitter=30)  
    scheduler.add_job(func=status_wallets.update, name="wallets", trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_plotnfts.update, name="plotnfts", trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_blockchains.update, name="blockchains", trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_connections.update, name="connections", trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_keys.update, name="keys", trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_alerts.update, name="alerts", trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_pools.update, name="pools", trigger='interval', seconds=60, jitter=30)
    scheduler.add_job(func=status_partials.update, name="partials", trigger='interval', seconds=60, jitter=30) 
        
    #scheduler.add_job(func=status_points.update, name="points", trigger='interval', seconds=10, jitter=0) 
    app.logger.debug("Starting background scheduler...")
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())