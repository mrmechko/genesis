import progressbar


def get_bar(title="progress", redirect_stdout=False):
    return progressbar.ProgressBar(
        widgets=[title, ' [', progressbar.Timer(), ']', progressbar.Bar(), '(', progressbar.ETA(), ')'],
        redirect_stdout=redirect_stdout
    )
