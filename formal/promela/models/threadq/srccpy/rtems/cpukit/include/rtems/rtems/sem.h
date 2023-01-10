/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @brief This header file defines the Semaphore Manager API.
 */

/*
 * Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)
 * Copyright (C) 1988, 2008 On-Line Applications Research Corporation (OAR)
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * This file is part of the RTEMS quality process and was automatically
 * generated.  If you find something that needs to be fixed or
 * worded better please post a report or patch to an RTEMS mailing list
 * or raise a bug report:
 *
 * https://docs.rtems.org/branches/master/user/support/bugs.html
 *
 * For information on updating and regenerating please refer to:
 *
 * https://docs.rtems.org/branches/master/eng/req/howto.html
 */

/* Generated from spec:/rtems/sem/if/header */

#ifndef _RTEMS_RTEMS_SEM_H
#define _RTEMS_RTEMS_SEM_H

#include <stdint.h>
#include <rtems/rtems/attr.h>
#include <rtems/rtems/options.h>
#include <rtems/rtems/status.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/types.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Generated from spec:/rtems/sem/if/group */

/**
 * @defgroup RTEMSAPIClassicSem Semaphore Manager
 *
 * @ingroup RTEMSAPIClassic
 *
 * @brief The Semaphore Manager utilizes standard Dijkstra counting semaphores
 *   to provide synchronization and mutual exclusion capabilities.
 */

/* Generated from spec:/rtems/sem/if/create */

/**
 * @ingroup RTEMSAPIClassicSem
 *
 * @brief Creates a semaphore with the specified properties and returns its
 *   identifier.
 *
 * This directive creates a semaphore which resides on the local node.  The new
 * semaphore has the user-defined name specified in ``name`` and the initial
 * count specified in ``count``.  For control and maintenance of the semaphore,
 * RTEMS allocates and initializes a SMCB.  The RTEMS-assigned semaphore
 * identifier is returned in ``id``.  This semaphore identifier is used with
 * other semaphore related directives to access the semaphore.
 *
 * The attribute set specified in ``attribute_set`` defines
 *
 * * the scope of the semaphore (local or global),
 *
 * * the discipline of the task wait queue used by the semaphore (FIFO or
 *   priority),
 *
 * * the class of the semaphore (counting, binary, or simple binary), and
 *
 * * the locking protocol of a binary semaphore (priority inheritance, priority
 *   ceiling or MrsP).
 *
 * The attribute set is built through a *bitwise or* of the attribute constants
 * described below.  Not all combinations of attributes are allowed.  Some
 * attributes are mutually exclusive.  If mutually exclusive attributes are
 * combined, the behaviour is undefined.
 *
 * The *scope of a semaphore* is either the local node only (local scope) or
 * all nodes in a multiprocessing network (global scope).  The scope is
 * selected by the mutually exclusive #RTEMS_LOCAL and #RTEMS_GLOBAL
 * attributes.
 *
 * * The local scope is the default and can be emphasized through use of the
 *   #RTEMS_LOCAL attribute.
 *
 * * The global scope is selected by the #RTEMS_GLOBAL attribute.  In a single
 *   node system and the local and global scope are identical.
 *
 * The *task wait queue discipline* is selected by the mutually exclusive
 * #RTEMS_FIFO and #RTEMS_PRIORITY attributes.
 *
 * * The FIFO discipline is the default and can be emphasized through use of
 *   the #RTEMS_FIFO attribute.
 *
 * * The priority discipline is selected by the #RTEMS_PRIORITY attribute.
 *   Some locking protocols require the priority discipline.
 *
 * The *semaphore class* is selected by the mutually exclusive
 * #RTEMS_COUNTING_SEMAPHORE, #RTEMS_BINARY_SEMAPHORE, and
 * #RTEMS_SIMPLE_BINARY_SEMAPHORE attributes.
 *
 * * Counting semaphores are the default and can be emphasized through use of
 *   the #RTEMS_COUNTING_SEMAPHORE attribute.
 *
 * * Binary semaphores are mutual exclusion (mutex) synchronization primitives
 *   which may have an owner.  The count of a binary semaphore is restricted to
 *   0 and 1.  The binary semaphore class is selected by the
 *   #RTEMS_BINARY_SEMAPHORE attribute.
 *
 * * Simple binary semaphores have no owner.  The count of a simple binary
 *   semaphore is restricted to 0 and 1.  They may be used for task and
 *   interrupt synchronization.  The simple binary semaphore class is selected
 *   by the #RTEMS_SIMPLE_BINARY_SEMAPHORE attribute.
 *
 * Binary semaphores may use a *locking protocol*.  If a locking protocol is
 * selected, then the scope shall be local and the priority task wait queue
 * discipline shall be selected.  The locking protocol is selected by the
 * mutually exclusive #RTEMS_INHERIT_PRIORITY, #RTEMS_PRIORITY_CEILING, and
 * #RTEMS_MULTIPROCESSOR_RESOURCE_SHARING attributes.
 *
 * * The default is to use no locking protocol.
 *
 * * The #RTEMS_INHERIT_PRIORITY attribute selects the priority inheritance
 *   locking protocol.
 *
 * * The #RTEMS_PRIORITY_CEILING attribute selects the priority ceiling locking
 *   protocol.  For this locking protocol a priority ceiling shall be specified
 *   in ``priority_ceiling``.
 *
 * * The #RTEMS_MULTIPROCESSOR_RESOURCE_SHARING attribute selects the MrsP
 *   locking protocol in SMP configurations, otherwise it selects the priority
 *   ceiling protocol.  For this locking protocol a priority ceiling shall be
 *   specified in ``priority_ceiling``.  This priority is used to set the
 *   priority ceiling in all scheduler instances.  This can be changed later
 *   with the rtems_semaphore_set_priority() directive using the returned
 *   semaphore identifier.
 *
 * This directive may cause the calling task to be preempted due to an obtain
 * and release of the object allocator mutex.
 *
 * Semaphores should not be made global unless remote tasks must interact with
 * the new semaphore.  This is to avoid the system overhead incurred by the
 * creation of a global semaphore.  When a global semaphore is created, the
 * semaphore's name and identifier must be transmitted to every node in the
 * system for insertion in the local copy of the global object table.
 *
 * The total number of global objects, including semaphores, is limited by the
 * #CONFIGURE_MP_MAXIMUM_GLOBAL_OBJECTS application configuration option.
 *
 * It is not allowed to create an initially locked MrsP semaphore and the
 * ::RTEMS_INVALID_NUMBER status code will be returned in SMP configurations in
 * this case.  This prevents lock order reversal problems with the allocator
 * mutex.
 *
 * @param name is the object name of the new semaphore.
 *
 * @param count is the initial count of the new semaphore.  If the semaphore is
 *   a mutex, then a count of 0 will make the calling task the owner of the new
 *   mutex and a count of 1 will create a mutex without an owner.
 *
 * @param attribute_set is the attribute set which defines the properties of
 *   the new semaphore.
 *
 * @param priority_ceiling is the priority ceiling if the new semaphore is a
 *   binary semaphore with the priority ceiling or MrsP semaphore locking
 *   protocol as defined by the attribute set.
 *
 * @param[out] id is the pointer to an object identifier variable.  The object
 *   identifier of the new semaphore will be stored in this variable, in case
 *   of a successful operation.
 *
 * @retval ::RTEMS_SUCCESSFUL The requested operation was successful.
 *
 * @retval ::RTEMS_INVALID_ADDRESS The ``priority_ceiling`` parameter was NULL.
 *
 * @retval ::RTEMS_INVALID_NAME The semaphore name was invalid.
 *
 * @retval ::RTEMS_INVALID_PRIORITY The priority ceiling was invalid.
 *
 * @retval ::RTEMS_NOT_DEFINED The attribute set was invalid.
 *
 * @retval ::RTEMS_TOO_MANY There was no inactive semaphore object available to
 *   create a new semaphore.  The semaphore object maximum is defined by the
 *   #CONFIGURE_MAXIMUM_SEMAPHORES application configuration option.
 *
 * @retval ::RTEMS_TOO_MANY In multiprocessing configurations, there was no
 *   inactive global object available to create a new global semaphore.
 */
rtems_status_code rtems_semaphore_create(
  rtems_name          name,
  uint32_t            count,
  rtems_attribute     attribute_set,
  rtems_task_priority priority_ceiling,
  rtems_id           *id
);

/* Generated from spec:/rtems/sem/if/delete */

/**
 * @ingroup RTEMSAPIClassicSem
 *
 * @brief %
 *
 * @param id %
 */
rtems_status_code rtems_semaphore_delete( rtems_id id );

/* Generated from spec:/rtems/sem/if/flush */

/**
 * @ingroup RTEMSAPIClassicSem
 *
 * @brief %
 *
 * @param id %
 */
rtems_status_code rtems_semaphore_flush( rtems_id id );

/* Generated from spec:/rtems/sem/if/ident */

/**
 * @ingroup RTEMSAPIClassicSem
 *
 * @brief Identifies a semaphore object by the specified object name.
 *
 * This directive obtains the semaphore identifier associated with the
 * semaphore name specified in ``name``.
 *
 * The node to search is specified in ``node``.  It shall be
 *
 * * a valid node number,
 *
 * * the constant #RTEMS_SEARCH_ALL_NODES to search in all nodes,
 *
 * * the constant #RTEMS_SEARCH_LOCAL_NODE to search in the local node only, or
 *
 * * the constant #RTEMS_SEARCH_OTHER_NODES to search in all nodes except the
 *   local node.
 *
 * If the semaphore name is not unique, then the semaphore identifier will
 * match the first semaphore with that name in the search order.  However, this
 * semaphore identifier is not guaranteed to correspond to the desired
 * semaphore.  The semaphore identifier is used with other semaphore related
 * directives to access the semaphore.
 *
 * If node is #RTEMS_SEARCH_ALL_NODES, all nodes are searched with the local
 * node being searched first.  All other nodes are searched with the lowest
 * numbered node searched first.
 *
 * If node is a valid node number which does not represent the local node, then
 * only the semaphores exported by the designated node are searched.
 *
 * This directive does not generate activity on remote nodes.  It accesses only
 * the local copy of the global object table.
 *
 * @param name is the object name to look up.
 *
 * @param node is the node or node set to search for a matching object.
 *
 * @param[out] id is the pointer to an object identifier variable.  The object
 *   identifier of an object with the specified name will be stored in this
 *   variable, in case of a successful operation.
 *
 * @retval ::RTEMS_SUCCESSFUL The requested operation was successful.
 *
 * @retval ::RTEMS_INVALID_ADDRESS The ``id`` parameter was NULL.
 *
 * @retval ::RTEMS_INVALID_NAME The ``name`` parameter was 0.
 *
 * @retval ::RTEMS_INVALID_NAME There was no object with the specified name on
 *   the specified nodes.
 *
 * @retval ::RTEMS_INVALID_NODE In multiprocessing configurations, the
 *   specified node was invalid.
 */
rtems_status_code rtems_semaphore_ident(
  rtems_name name,
  uint32_t   node,
  rtems_id  *id
);

/* Generated from spec:/rtems/sem/if/obtain */

/**
 * @ingroup RTEMSAPIClassicSem
 *
 * @brief %
 *
 * @param id %
 *
 * @param option_set %
 *
 * @param timeout %
 */
rtems_status_code rtems_semaphore_obtain(
  rtems_id       id,
  rtems_option   option_set,
  rtems_interval timeout
);

/* Generated from spec:/rtems/sem/if/release */

/**
 * @ingroup RTEMSAPIClassicSem
 *
 * @brief %
 *
 * @param id %
 */
rtems_status_code rtems_semaphore_release( rtems_id id );

/* Generated from spec:/rtems/sem/if/set-priority */

/**
 * @ingroup RTEMSAPIClassicSem
 *
 * @brief %
 *
 * @param semaphore_id %
 *
 * @param scheduler_id %
 *
 * @param new_priority %
 *
 * @param old_priority %
 */
rtems_status_code rtems_semaphore_set_priority(
  rtems_id             semaphore_id,
  rtems_id             scheduler_id,
  rtems_task_priority  new_priority,
  rtems_task_priority *old_priority
);

#ifdef __cplusplus
}
#endif

#endif /* _RTEMS_RTEMS_SEM_H */
