#!/usr/bin/env python3
import sys
from photo_date_changer.cli import main

if __name__ == '__main__':
    # Inject the --gui flag if it's not already present
    if '--gui' not in sys.argv:
        sys.argv.append('--gui')
    main()
