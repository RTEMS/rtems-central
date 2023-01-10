# RTEMS Promela Models

`formal/promela/models/'

This directory contains formal models written in Promela to support test generation.

## Contributors

* Andrew Butterfield
* Frédéric Tuong
* Robert Jennings
* Jerzy Jaśkuć
* Eoin Lynch

## License

This project is licensed under the
[BSD-2-Clause](https://spdx.org/licenses/BSD-2-Clause.html) or
[CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html).

## Models Overview

There are currently five models present. Four are test-generation ready, whilst the fifth is still work in progress.

We identify the usual RTEMS name for the component,
the Promela "model-name", and the path to the model directory.

* Barrier Manager: "barrier-mgr-model" `formal/promela/models/barriers`
* Chains API:  "chains-api-model" `formal/promela/models/chains`
* Event Manager "event-mgr-model" `formal/promela/models/events`
* Message Manager "msg-mgr-model" `formal/promela/models/messages`
* MrsP Thread Queues "mrsp-threadq-model" `formal/promela/models/threadq`

## Doing Test Generation

Ensure that the virtual environment defined in `formal/promela/src/env` is active.

We shall assume that the alias `tb` has been defined as suggested in  `formal/promela/src/README.md`.

Simply enter the relevant model sub-directory and invoke `tb` from the command line with desired command line arguments.

A simple sequence that clears out all previously generated tests (from all models), clears all generated artifacts from this model,
and then does the whole test generation process is:

```
tb zero
tb clean
tb all <model-name>
```

This will produce a test report in `<testsuite>-test.log`.


