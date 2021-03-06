#
#  Copyright (C) 2014 Dell, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from blockade.tests import unittest
from blockade.errors import BlockadeConfigError
from blockade.config import BlockadeConfig, BlockadeContainerConfig, \
    dependency_sorted


class ConfigTests(unittest.TestCase):

    def test_parse_1(self):
        containers = {
            "c1": {"image": "image1", "command": "/bin/bash"},
            "c2": {"image": "image2", "links": ["c1"]}
        }
        d = dict(containers=containers)

        config = BlockadeConfig.from_dict(d)
        self.assertEqual(len(config.containers), 2)
        self.assertEqual(config.containers["c1"].name, "c1")
        self.assertEqual(config.containers["c1"].image, "image1")
        self.assertEqual(config.containers["c1"].command, "/bin/bash")
        self.assertEqual(config.containers["c2"].name, "c2")
        self.assertEqual(config.containers["c2"].image, "image2")

    def test_parse_2(self):
        containers = {
            "c1": {"image": "image1", "command": "/bin/bash"}
        }
        network = {"flaky": "61%"}
        d = dict(containers=containers, network=network)

        config = BlockadeConfig.from_dict(d)
        # default value should be there
        self.assertIn("flaky", config.network)
        self.assertEqual(config.network['flaky'], "61%")
        # default value should be there
        self.assertIn("slow", config.network)

    def test_parse_with_volumes_1(self):
        containers = {
            "c1": {"image": "image1", "command": "/bin/bash",
                   "volumes": {"/some/mount": "/some/place"}}
        }
        network = {}
        d = dict(containers=containers, network=network)

        config = BlockadeConfig.from_dict(d)
        # default value should be there
        self.assertEqual(len(config.containers), 1)
        c1 = config.containers['c1']
        self.assertEqual(c1.volumes, {"/some/mount": "/some/place"})

    def test_parse_with_volumes_2(self):
        containers = {
            "c1": {"image": "image1", "command": "/bin/bash",
                   "volumes": ["/some/mount"]}
        }
        network = {}
        d = dict(containers=containers, network=network)

        config = BlockadeConfig.from_dict(d)
        # default value should be there
        self.assertEqual(len(config.containers), 1)
        c1 = config.containers['c1']
        self.assertEqual(c1.volumes, {"/some/mount": "/some/mount"})

    def test_parse_with_volumes_3(self):
        containers = {
            "c1": {"image": "image1", "command": "/bin/bash",
                   "volumes": {"/some/mount": ""}}
        }
        network = {}
        d = dict(containers=containers, network=network)

        config = BlockadeConfig.from_dict(d)
        # default value should be there
        self.assertEqual(len(config.containers), 1)
        c1 = config.containers['c1']
        self.assertEqual(c1.volumes, {"/some/mount": "/some/mount"})

    def test_parse_with_volumes_4(self):
        containers = {
            "c1": {"image": "image1", "command": "/bin/bash",
                   "volumes": {"/some/mount": None}}
        }
        network = {}
        d = dict(containers=containers, network=network)

        config = BlockadeConfig.from_dict(d)
        # default value should be there
        self.assertEqual(len(config.containers), 1)
        c1 = config.containers['c1']
        self.assertEqual(c1.volumes, {"/some/mount": "/some/mount"})

    def test_parse_with_env_1(self):
        containers = {
            "c1": {"image": "image1", "command": "/bin/bash",
                   "environment": {"HATS": 4, "JACKETS": "some"}}
        }
        d = dict(containers=containers, network={})

        config = BlockadeConfig.from_dict(d)
        self.assertEqual(len(config.containers), 1)
        c1 = config.containers['c1']
        self.assertEqual(c1.environment, {"HATS": 4, "JACKETS": "some"})

    def test_parse_with_numeric_port(self):
        containers = {
            "c1": {"image": "image1", "command": "/bin/bash",
                   "ports": [10000]}
        }
        d = dict(containers=containers, network={})

        config = BlockadeConfig.from_dict(d)
        self.assertEqual(len(config.containers), 1)
        c1 = config.containers['c1']
        self.assertEqual(c1.ports, {"10000": "10000"})

    def test_parse_fail_1(self):
        containers = {
            "c1": {"image": "image1", "command": "/bin/bash"},
            "c2": {"image": "image2", "links": ["c1"]}
        }
        d = dict(contianers=containers)
        with self.assertRaises(BlockadeConfigError):
            BlockadeConfig.from_dict(d)

    def test_parse_fail_2(self):
        containers = {
            "c1": {"ima": "image1", "command": "/bin/bash"},
            "c2": {"image": "image2", "links": ["c1"]}
        }
        d = dict(containers=containers)
        with self.assertRaises(BlockadeConfigError):
            BlockadeConfig.from_dict(d)

    def test_link_ordering_1(self):
        containers = [BlockadeContainerConfig("c1", "image"),
                      BlockadeContainerConfig("c2", "image"),
                      BlockadeContainerConfig("c3", "image")]
        ordered = dependency_sorted(containers)
        ordered_names = [c.name for c in ordered]
        self.assertDependencyLevels(ordered_names, ["c1", "c2", "c3"])

    def test_link_ordering_2(self):
        containers = [BlockadeContainerConfig("c1", "image"),
                      BlockadeContainerConfig("c2", "image",
                                              links={"c1": "c1"}),
                      BlockadeContainerConfig("c3", "image")]
        ordered = dependency_sorted(containers)
        ordered_names = [c.name for c in ordered]
        self.assertDependencyLevels(ordered_names,
                                    ["c1", "c3"],
                                    ["c2"])

    def test_link_ordering_3(self):
        containers = [BlockadeContainerConfig("c1", "image"),
                      BlockadeContainerConfig("c2", "image",
                                              links={"c1": "c1"}),
                      BlockadeContainerConfig("c3", "image",
                                              links={"c1": "c1"})]
        ordered = dependency_sorted(containers)
        ordered_names = [c.name for c in ordered]
        self.assertDependencyLevels(ordered_names, ["c1"], ["c2", "c3"])

    def test_link_ordering_4(self):
        containers = [BlockadeContainerConfig("c1", "image"),
                      BlockadeContainerConfig("c2", "image", links=["c1"]),
                      BlockadeContainerConfig("c3", "image", links=["c1"]),
                      BlockadeContainerConfig("c4", "image",
                                              links=["c1", "c3"]),
                      BlockadeContainerConfig("c5", "image",
                                              links=["c2", "c3"]),
                      ]
        ordered = dependency_sorted(containers)
        ordered_names = [c.name for c in ordered]
        self.assertDependencyLevels(ordered_names, ["c1"], ["c2", "c3"],
                                    ["c4", "c5"])

    def test_link_ordering_unknown_1(self):
        containers = [BlockadeContainerConfig("c1", "image"),
                      BlockadeContainerConfig("c2", "image", links=["c6"]),
                      BlockadeContainerConfig("c3", "image", links=["c1"])]
        with self.assertRaisesRegexp(BlockadeConfigError, "unknown"):
            dependency_sorted(containers)

    def test_link_ordering_unknown_2(self):
        containers = [BlockadeContainerConfig("c1", "image"),
                      BlockadeContainerConfig("c2", "image",
                                              links=["c6", "c7"]),
                      BlockadeContainerConfig("c3", "image", links=["c1"])]
        with self.assertRaisesRegexp(BlockadeConfigError, "unknown"):
            dependency_sorted(containers)

    def test_link_ordering_circular_1(self):
        containers = [BlockadeContainerConfig("c1", "image"),
                      BlockadeContainerConfig("c2", "image", links=["c1"]),
                      BlockadeContainerConfig("c3", "image", links=["c3"])]

        with self.assertRaisesRegexp(BlockadeConfigError, "circular"):
            dependency_sorted(containers)

    def test_link_ordering_circular_2(self):
        containers = [BlockadeContainerConfig("c1", "image"),
                      BlockadeContainerConfig("c2", "image",
                                              links=["c1", "c3"]),
                      BlockadeContainerConfig("c3", "image", links=["c2"])]

        with self.assertRaisesRegexp(BlockadeConfigError, "circular"):
            dependency_sorted(containers)

    def assertDependencyLevels(self, seq, *levels):
        self.assertEquals(len(seq), sum(len(l) for l in levels))

        for index, level in enumerate(levels):
            expected = set(level)
            actual = set(seq[:len(level)])
            if expected != actual:
                self.fail("Expected dep level #%d %s but got %s. Sequence: %s" % (index+1, expected, actual, seq))
            seq = seq[len(level):]

