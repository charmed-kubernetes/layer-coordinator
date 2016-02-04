# Copyright 2015-2016 Canonical Ltd.
#
# This file is part of the Coordinator Layer for Juju.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from charmhelpers.coordinator import BaseCoordinator
from charms import reactive


coordinator = None  # The BaseCoordinator, initialized by bootstrap.py


def acquire(lock):
    """
    Sets either the coordinator.granted.{lockname} or
    coordinator.requested.{lockname} state.

    Returns True if the lock could be immediately granted.

    If locks cannot be granted immediately, they will be granted
    in a future hook and the coordinator.granted.{lockname} state set.
    """
    global coordinator
    if coordinator.acquire(lock):
        reactive.set_state('coordinator.granted.{}'.format(lock))
        return True
    else:
        reactive.set_state('coordinator.requested.{}'.format(lock))
        return False


class SimpleCoordinator(BaseCoordinator):
    '''A simple BaseCoordinator that is suitable for almost all cases.

    Only one unit at a time will be granted locks. All requests by that
    unit will be granted. So only one unit may run tasks guarded by a lock,
    and the lock name is irrelevant.
    '''
    def default_grant(self, lock, unit, granted, queue):
        '''Grant locks to only one unit at a time, regardless of the lock name.

        This lets us keep separate locks like join and restart,
        while ensuring the operations do not occur on different nodes
        at the same time.
        '''
        # Return True if this unit has already been granted any lock.
        if 'unit' in self.grants:
            return True

        # Return False if another unit has been granted any lock.
        if self.grants:
            return False

        # Otherwise, return True if the unit is first in the queue for
        # this named lock.
        return queue[0] == unit