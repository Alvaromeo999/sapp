# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import io
import unittest
from typing import Iterable, Union

from ...analysis_output import AnalysisOutput, Metadata
from .. import (
    ParseConditionTuple,
    ParseIssueConditionTuple,
    ParseIssueTuple,
    ParseTraceFeature,
    SourceLocation,
)
from ..base_parser import ParseType
from ..mariana_trench_parser import Parser


class TestParser(unittest.TestCase):
    def assertParsed(
        self,
        output: str,
        expected: Iterable[Union[ParseConditionTuple, ParseIssueTuple]],
    ) -> None:
        output = "".join(output.split("\n"))  # Flatten json-line.
        parser = Parser()
        analysis_output = AnalysisOutput(
            directory="/output/directory",
            filename_specs=["models.json"],
            file_handle=io.StringIO(output),
            metadata=Metadata(
                repo_roots={"/analysis/root"},
                analysis_tool_version="0.2",
                rules={1: {"name": "TestRule", "description": "Test Rule Description"}},
            ),
        )

        def sort_entry(e: Union[ParseConditionTuple, ParseIssueTuple]) -> str:
            if isinstance(e, ParseConditionTuple):
                return e.caller
            else:
                return e.callable

        self.assertEqual(
            sorted(parser.parse(analysis_output), key=sort_entry),
            expected,
        )

    def testEmptyModels(self) -> None:
        self.assertParsed(
            """
            {
              "method": "LClass;.method:()V",
              "position": {
                "line": 1,
                "path": "Class.java"
              }
            }
            """,
            [],
        )

    def testModelWithIssue(self) -> None:
        self.assertParsed(
            """
            {
              "method": "LClass;.flow:()V",
              "issues": [
                {
                  "rule": 1,
                  "position": {
                    "path": "Flow.java",
                    "line": 10,
                    "start": 11,
                    "end": 12
                  },
                  "callee": "LSink;.sink:(LData;)V",
                  "sink_index": 0,
                  "sinks": [
                    {
                      "call": {
                        "resolves_to": "LSink;.sink:(LData;)V",
                        "port": "Argument(1)",
                        "position": {
                          "path": "Flow.java",
                          "line": 10,
                          "start": 11,
                          "end": 12
                        }
                      },
                      "kinds": [
                        {
                          "distance": 2,
                          "always_features": ["via-parameter-field"],
                          "kind": "TestSink",
                          "origins": [
                            {
                              "method": "LSink;.sink:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_positions": [{"line": 13, "start": 14, "end": 15}],
                      "local_features": { "always_features": ["via-parameter-field"] }
                    }
                  ],
                  "sources": [
                    {
                      "call": {
                        "resolves_to": "LSource;.source:()LData;",
                        "port": "Return",
                        "position": {
                          "path": "Flow.java",
                          "line": 20,
                          "start": 21,
                          "end": 22
                        }
                      },
                      "kinds": [
                        {
                          "distance": 3,
                          "may_features": ["via-obscure"],
                          "kind": "TestSource",
                          "origins": [
                            {
                              "method": "LSource;.source:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_positions": [
                        {"line": 23, "start": 24, "end": 25},
                        {"line": 26, "start": 27, "end": 28}
                      ]
                    }
                  ],
                  "may_features": ["via-obscure"],
                  "always_features": ["via-parameter-field"]
                }
              ],
              "position": {
                "line": 2,
                "path": "Flow.java"
              }
            }
            """,
            [
                ParseIssueTuple(
                    code=1,
                    message="TestRule: Test Rule Description",
                    callable="LClass;.flow:()V",
                    handle="LClass;.flow:()V:LSink;.sink:(LData;)V:0:1:1ef9022f932a64d0",
                    filename="Flow.java",
                    callable_line=2,
                    line=10,
                    start=12,
                    end=13,
                    preconditions=[
                        ParseIssueConditionTuple(
                            callee="LSink;.sink:(LData;)V",
                            port="argument(1)",
                            location=SourceLocation(
                                line_no=10,
                                begin_column=12,
                                end_column=13,
                            ),
                            leaves=[("TestSink", 2)],
                            titos=[
                                SourceLocation(
                                    line_no=13, begin_column=15, end_column=16
                                )
                            ],
                            features=[
                                ParseTraceFeature("always-via-parameter-field", []),
                            ],
                            type_interval=None,
                            annotations=[],
                        )
                    ],
                    postconditions=[
                        ParseIssueConditionTuple(
                            callee="LSource;.source:()LData;",
                            port="result",
                            location=SourceLocation(
                                line_no=20,
                                begin_column=22,
                                end_column=23,
                            ),
                            leaves=[("TestSource", 3)],
                            titos=[
                                SourceLocation(
                                    line_no=23, begin_column=25, end_column=26
                                ),
                                SourceLocation(
                                    line_no=26, begin_column=28, end_column=29
                                ),
                            ],
                            features=[],
                            type_interval=None,
                            annotations=[],
                        )
                    ],
                    initial_sources={("LSource;.source:(LData;)V", "TestSource", 3)},
                    final_sinks={("LSink;.sink:(LData;)V", "TestSink", 2)},
                    features=[
                        "always-via-parameter-field",
                        "via-obscure",
                    ],
                    fix_info=None,
                )
            ],
        )
        self.assertParsed(
            """
            {
              "method": "LClass;.flow:()V",
              "issues": [
                {
                  "rule": 1,
                  "position": {
                    "path": "Flow.java",
                    "line": 10,
                    "start": 11,
                    "end": 12
                  },
                  "callee": "LSink;.sink:(LData;)V",
                  "sink_index": 1,
                  "sinks": [
                    {
                      "call": {
                        "resolves_to": "LSink;.sink:(LData;)V",
                        "port": "Argument(1)",
                        "position": {
                          "path": "Flow.java",
                          "line": 10,
                          "start": 11,
                          "end": 12
                        }
                      },
                      "kinds": [
                        {
                          "distance": 2,
                          "always_features": ["via-parameter-field"],
                          "kind": "TestSink",
                          "origins": [
                            {
                              "method": "LSink;.sink:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_positions": [{"line": 13, "start": 14, "end": 15}]
                    },
                    {
                      "call": {
                        "resolves_to": "LSink;.sink:(LData;)V",
                        "port": "Argument(1)",
                        "position": {
                          "path": "Flow.java",
                          "line": 20,
                          "start": 21,
                          "end": 22
                        }
                      },
                      "kinds": [
                        {
                          "distance": 3,
                          "always_features": ["via-obscure"],
                          "kind": "TestSink",
                          "origins": [
                            {
                              "method": "LSink;.other_sink:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ]
                    }
                  ],
                  "sources": [
                    {
                      "call": {
                        "resolves_to": "LSource;.source:()LData;",
                        "port": "Return",
                        "position": {
                          "path": "Flow.java",
                          "line": 30,
                          "start": 31,
                          "end": 32
                        }
                      },
                      "kinds": [
                        {
                          "distance": 3,
                          "kind": "TestSource",
                          "origins": [
                            {
                              "method": "LSource;.source:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_positions": [{"line": 33, "start": 34, "end": 35}],
                      "local_features": {"always_features": ["via-obscure"]}
                   }
                  ],
                  "may_features": ["via-obscure", "via-parameter-field"]
                }
              ],
              "position": {
                "line": 2,
                "path": "Flow.java"
              }
            }
            """,
            [
                ParseIssueTuple(
                    code=1,
                    message="TestRule: Test Rule Description",
                    callable="LClass;.flow:()V",
                    handle="LClass;.flow:()V:LSink;.sink:(LData;)V:1:1:e7653955345a4ce9",
                    filename="Flow.java",
                    callable_line=2,
                    line=10,
                    start=12,
                    end=13,
                    preconditions=[
                        ParseIssueConditionTuple(
                            callee="LSink;.sink:(LData;)V",
                            port="argument(1)",
                            location=SourceLocation(
                                line_no=10,
                                begin_column=12,
                                end_column=13,
                            ),
                            leaves=[("TestSink", 2)],
                            titos=[
                                SourceLocation(
                                    line_no=13, begin_column=15, end_column=16
                                )
                            ],
                            features=[],
                            type_interval=None,
                            annotations=[],
                        ),
                        ParseIssueConditionTuple(
                            callee="LSink;.sink:(LData;)V",
                            port="argument(1)",
                            location=SourceLocation(
                                line_no=20,
                                begin_column=22,
                                end_column=23,
                            ),
                            leaves=[("TestSink", 3)],
                            titos=[],
                            features=[],
                            type_interval=None,
                            annotations=[],
                        ),
                    ],
                    postconditions=[
                        ParseIssueConditionTuple(
                            callee="LSource;.source:()LData;",
                            port="result",
                            location=SourceLocation(
                                line_no=30,
                                begin_column=32,
                                end_column=33,
                            ),
                            leaves=[("TestSource", 3)],
                            titos=[
                                SourceLocation(
                                    line_no=33, begin_column=35, end_column=36
                                )
                            ],
                            features=[ParseTraceFeature("always-via-obscure", [])],
                            type_interval=None,
                            annotations=[],
                        )
                    ],
                    initial_sources={("LSource;.source:(LData;)V", "TestSource", 3)},
                    final_sinks={
                        ("LSink;.sink:(LData;)V", "TestSink", 2),
                        ("LSink;.other_sink:(LData;)V", "TestSink", 3),
                    },
                    features=["via-obscure", "via-parameter-field"],
                    fix_info=None,
                )
            ],
        )
        self.assertParsed(
            """
            {
              "method": "LClass;.flow:()V",
              "issues": [
                {
                  "rule": 1,
                  "position": {
                    "path": "Flow.java",
                    "line": 10,
                    "start": 11,
                    "end": 12
                  },
                  "callee": "LSink;.sink:(LData;)V",
                  "sink_index": 2,
                  "sinks": [
                    {
                      "call": {
                        "resolves_to": "LSink;.sink:(LData;)V",
                        "port": "Argument(1)",
                        "position": {
                          "path": "Flow.java",
                          "line": 10,
                          "start": 11,
                          "end": 12
                        }
                      },
                      "kinds": [
                        {
                          "distance": 2,
                          "always_features": ["via-parameter-field"],
                          "kind": "TestSink",
                          "origins": [
                            {
                              "method": "LSink;.sink:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_positions": [{"line": 13, "start": 14, "end": 15}]
                  }
                  ],
                  "sources": [
                    {
                      "kinds": [
                        {
                          "distance": 0,
                          "kind": "TestSource",
                          "origins": [
                            { "field": "LSource;.sourceField:LData;" }
                          ]
                        }
                      ],
                      "local_positions": [{"line": 33, "start": 34, "end": 35}]
                    }
                  ],
                  "may_features": ["via-obscure", "via-parameter-field"]
                }
              ],
              "position": {
                "line": 2,
                "path": "Flow.java"
              }
            }
            """,
            [
                ParseIssueTuple(
                    code=1,
                    message="TestRule: Test Rule Description",
                    callable="LClass;.flow:()V",
                    handle="LClass;.flow:()V:LSink;.sink:(LData;)V:2:1:4a78c3ad238e0bf7",
                    filename="Flow.java",
                    callable_line=2,
                    line=10,
                    start=12,
                    end=13,
                    preconditions=[
                        ParseIssueConditionTuple(
                            callee="LSink;.sink:(LData;)V",
                            port="argument(1)",
                            location=SourceLocation(
                                line_no=10,
                                begin_column=12,
                                end_column=13,
                            ),
                            leaves=[("TestSink", 2)],
                            titos=[
                                SourceLocation(
                                    line_no=13, begin_column=15, end_column=16
                                )
                            ],
                            features=[],
                            type_interval=None,
                            annotations=[],
                        )
                    ],
                    postconditions=[
                        ParseIssueConditionTuple(
                            callee="leaf",
                            port="source",
                            location=SourceLocation(
                                line_no=2,
                                begin_column=1,
                                end_column=1,
                            ),
                            leaves=[("TestSource", 0)],
                            titos=[
                                SourceLocation(
                                    line_no=33, begin_column=35, end_column=36
                                )
                            ],
                            features=[],
                            type_interval=None,
                            annotations=[],
                        )
                    ],
                    initial_sources={("LSource;.sourceField:LData;", "TestSource", 0)},
                    final_sinks={
                        ("LSink;.sink:(LData;)V", "TestSink", 2),
                    },
                    features=["via-obscure", "via-parameter-field"],
                    fix_info=None,
                )
            ],
        )

        # Multiple callees, local_positions/features and kinds
        # (and origins within kinds)
        self.assertParsed(
            """
            {
              "method": "LClass;.flow:()V",
              "issues": [
                {
                  "rule": 1,
                  "position": {
                    "path": "Flow.java",
                    "line": 10,
                    "start": 11,
                    "end": 12
                  },
                  "callee": "LSink;.sink:(LData;)V",
                  "sink_index": 3,
                  "sinks": [
                    {
                      "call": {
                        "resolves_to": "LSink;.sink:(LData;)V",
                        "port": "Argument(1)",
                        "position": {
                          "path": "Flow.java",
                          "line": 10,
                          "start": 11,
                          "end": 12
                        }
                      },
                      "kinds": [
                        {
                          "distance": 2,
                          "always_features": ["via-parameter-field"],
                          "kind": "TestSink",
                          "origins": [
                            {
                              "method": "LSink;.sink:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_positions": [{"line": 13, "start": 14, "end": 15}]
                    },
                    {
                      "call": {
                        "resolves_to": "LSink;.sink2:(LData;)V",
                        "port": "Argument(1)",
                        "position": {
                          "path": "Flow.java",
                          "line": 11,
                          "start": 11,
                          "end": 12
                        }
                      },
                      "kinds": [
                        {
                          "distance": 3,
                          "kind": "TestSink",
                          "origins": [
                            {
                              "method": "LSink;.sink:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        },
                        {
                          "distance": 1,
                          "kind": "TestSink2",
                          "origins": [
                            {
                              "method": "LSink;.sink3:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_positions": [{"line": 14, "start": 14, "end": 15}]
                    }
                  ],
                  "sources": [
                    {
                      "call": {
                        "resolves_to": "LSource;.source:()LData;",
                        "port": "Return",
                        "position": {
                          "path": "Flow.java",
                          "line": 30,
                          "start": 31,
                          "end": 32
                        }
                      },
                      "kinds": [
                        {
                          "distance": 3,
                          "kind": "TestSource",
                          "origins": [
                            {
                              "method": "LSource;.source:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_positions": [{"line": 33, "start": 34, "end": 35}],
                      "local_features": {"always_features": ["via-obscure"]}
                    },
                    {
                      "call": {
                        "resolves_to": "LSource;.source2:()LData;",
                        "port": "Return",
                        "position": {
                          "path": "Flow.java",
                          "line": 31,
                          "start": 31,
                          "end": 32
                        }
                      },
                      "kinds": [
                        {
                          "distance": 4,
                          "kind": "TestSource",
                          "origins": [
                            {
                              "method": "LSource;.source:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        },
                        {
                          "distance": 5,
                          "kind": "TestSource2",
                          "origins": [
                            {
                              "method": "LSource;.source3:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ]
                    }
                  ],
                  "may_features": ["via-obscure", "via-parameter-field"]
                }
              ],
              "position": {
                "line": 2,
                "path": "Flow.java"
              }
            }
            """,
            [
                ParseIssueTuple(
                    code=1,
                    message="TestRule: Test Rule Description",
                    callable="LClass;.flow:()V",
                    handle="LClass;.flow:()V:LSink;.sink:(LData;)V:3:1:4172bb4962984471",
                    filename="Flow.java",
                    callable_line=2,
                    line=10,
                    start=12,
                    end=13,
                    preconditions=[
                        ParseIssueConditionTuple(
                            callee="LSink;.sink:(LData;)V",
                            port="argument(1)",
                            location=SourceLocation(
                                line_no=10,
                                begin_column=12,
                                end_column=13,
                            ),
                            leaves=[("TestSink", 2)],
                            titos=[
                                SourceLocation(
                                    line_no=13, begin_column=15, end_column=16
                                )
                            ],
                            features=[],
                            type_interval=None,
                            annotations=[],
                        ),
                        ParseIssueConditionTuple(
                            callee="LSink;.sink2:(LData;)V",
                            port="argument(1)",
                            location=SourceLocation(
                                line_no=11,
                                begin_column=12,
                                end_column=13,
                            ),
                            leaves=[("TestSink", 3), ("TestSink2", 1)],
                            titos=[
                                SourceLocation(
                                    line_no=14, begin_column=15, end_column=16
                                )
                            ],
                            features=[],
                            type_interval=None,
                            annotations=[],
                        ),
                    ],
                    postconditions=[
                        ParseIssueConditionTuple(
                            callee="LSource;.source:()LData;",
                            port="result",
                            location=SourceLocation(
                                line_no=30,
                                begin_column=32,
                                end_column=33,
                            ),
                            leaves=[("TestSource", 3)],
                            titos=[
                                SourceLocation(
                                    line_no=33, begin_column=35, end_column=36
                                )
                            ],
                            features=[ParseTraceFeature("always-via-obscure", [])],
                            type_interval=None,
                            annotations=[],
                        ),
                        ParseIssueConditionTuple(
                            callee="LSource;.source2:()LData;",
                            port="result",
                            location=SourceLocation(
                                line_no=31,
                                begin_column=32,
                                end_column=33,
                            ),
                            leaves=[("TestSource", 4), ("TestSource2", 5)],
                            titos=[],
                            features=[],
                            type_interval=None,
                            annotations=[],
                        ),
                    ],
                    initial_sources={
                        ("LSource;.source:(LData;)V", "TestSource", 3),
                        ("LSource;.source:(LData;)V", "TestSource", 4),
                        ("LSource;.source3:(LData;)V", "TestSource2", 5),
                    },
                    final_sinks={
                        ("LSink;.sink:(LData;)V", "TestSink", 2),
                        ("LSink;.sink:(LData;)V", "TestSink", 3),
                        ("LSink;.sink3:(LData;)V", "TestSink2", 1),
                    },
                    features=["via-obscure", "via-parameter-field"],
                    fix_info=None,
                )
            ],
        )

    def testIssueMasterHandles(self) -> None:
        self.assertEqual(
            Parser.get_master_handle(
                callable="LClass;.flow:()V",
                callee_signature="LSink;.sink:(LData;)V",
                sink_index=1,
                code=4,
                callable_line=2,
                issue_line=10,
            ),
            "LClass;.flow:()V:LSink;.sink:(LData;)V:1:4:794639b3826f7c38",
        )

        # Replace anonymous class callee numbers with the relative line
        # in the issue handle
        self.assertEqual(
            Parser.get_master_handle(
                callable="LClass;.flow:()V",
                callee_signature="LSink$2$10;.sink:(LData;)V",
                sink_index=2,
                code=1,
                callable_line=2,
                issue_line=10,
            ),
            "LClass;.flow:()V:LSink$$#8;.sink:(LData;)V:2:1:67e997f12486978a",
        )

        # Don't replace an inner class that is named rather than numbered and ignore $'s in the method name
        self.assertEqual(
            Parser.get_master_handle(
                callable="LClass;.flow:()V",
                callee_signature="LSink$Inner;.sink$default:(LData;)V",
                sink_index=0,
                code=1,
                callable_line=2,
                issue_line=10,
            ),
            "LClass;.flow:()V:LSink$Inner;.sink$default:(LData;)V:0:1:62c60c27a623a6f2",
        )

        # If the callable has an unknown line then default to replacement with -1
        self.assertEqual(
            Parser.get_master_handle(
                callable="LClass;.flow:()V",
                callee_signature="LSink$1;.sink:(LData;)V",
                sink_index=1,
                code=5,
                callable_line=-1,
                issue_line=-1,
            ),
            "LClass;.flow:()V:LSink$#-1;.sink:(LData;)V:1:5:c8fdde661b3ae0f5",
        )

    def testModelPostconditions(self) -> None:
        # Leaf case.
        self.assertParsed(
            """
            {
              "method": "LSource;.source:()V",
              "generations": [
                {
                  "port": "Return",
                  "taint": [
                    {
                      "kinds": [
                        {
                          "always_features": ["via-parameter-field"],
                          "kind": "TestSource",
                          "origins": [
                            {
                              "method": "LSource;.source:()V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_features": {
                        "always_features": ["via-obscure"],
                        "may_features": ["via-taint-in-taint-out"]
                      }
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Source.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.POSTCONDITION,
                    caller="LSource;.source:()V",
                    callee="leaf",
                    callee_location=SourceLocation(
                        line_no=1,
                        begin_column=1,
                        end_column=1,
                    ),
                    filename="Source.java",
                    titos=[],
                    leaves=[("TestSource", 0)],
                    caller_port="result",
                    callee_port="source",
                    type_interval=None,
                    features=[
                        ParseTraceFeature("always-via-obscure", []),
                        ParseTraceFeature("via-taint-in-taint-out", []),
                    ],
                    annotations=[],
                )
            ],
        )

        # Origin case.
        self.assertParsed(
            """
            {
              "method": "LClass;.indirect_source:()V",
              "generations": [
                {
                  "port": "Return",
                  "taint": [
                    {
                      "origin": {
                        "position": {
                          "path": "Class.java",
                          "line": 10,
                          "start": 11,
                          "end": 12
                        }
                      },
                      "kinds": [
                        {
                          "distance": 1,
                          "kind": "TestSource",
                          "origins": [
                            {
                              "method": "LSource;.source:()V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_positions": [
                        {"line": 13, "start": 14, "end": 15},
                        {"line": 16, "start": 17, "end": 18}
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Class.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.POSTCONDITION,
                    caller="LClass;.indirect_source:()V",
                    callee="leaf",
                    callee_location=SourceLocation(
                        line_no=10,
                        begin_column=12,
                        end_column=13,
                    ),
                    filename="Class.java",
                    titos=[
                        SourceLocation(line_no=13, begin_column=15, end_column=16),
                        SourceLocation(line_no=16, begin_column=18, end_column=19),
                    ],
                    leaves=[("TestSource", 1)],
                    caller_port="result",
                    callee_port="source",
                    type_interval=None,
                    features=[],
                    annotations=[],
                )
            ],
        )

        # Origin with name case.
        self.assertParsed(
            """
            {
              "method": "LClass;.indirect_source:()V",
              "generations": [
                {
                  "port": "Return",
                  "taint": [
                    {
                      "origin": {
                        "position": {
                          "path": "Class.java",
                          "line": 10,
                          "start": 11,
                          "end": 12
                        },
                        "method": "LSource;.source:()V"
                      },
                      "kinds": [
                        {
                          "distance": 1,
                          "kind": "TestSource",
                          "origins": [
                            {
                              "method": "LSource;.source:()V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_positions": [
                        {"line": 13, "start": 14, "end": 15},
                        {"line": 16, "start": 17, "end": 18}
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Class.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.POSTCONDITION,
                    caller="LClass;.indirect_source:()V",
                    callee="LSource;.source:()V",
                    callee_location=SourceLocation(
                        line_no=10,
                        begin_column=12,
                        end_column=13,
                    ),
                    filename="Class.java",
                    titos=[
                        SourceLocation(line_no=13, begin_column=15, end_column=16),
                        SourceLocation(line_no=16, begin_column=18, end_column=19),
                    ],
                    leaves=[("TestSource", 1)],
                    caller_port="result",
                    callee_port="source",
                    type_interval=None,
                    features=[],
                    annotations=[],
                )
            ],
        )

        # Origin with parameter type overrides.
        self.assertParsed(
            """
            {
              "method": "LClass;.indirect_source:()V",
              "generations": [
                {
                  "port": "Return",
                  "taint": [
                    {
                      "origin": {
                        "position": {
                          "path": "Class.java",
                          "line": 10,
                          "start": 11,
                          "end": 12
                        },
                        "method": {
                          "name": "LSource;.source:()V",
                          "parameter_type_overrides": [
                            {
                              "parameter": 0,
                              "type": "LAnonymous$0;"
                            },
                            {
                              "parameter": 1,
                              "type": "LAnonymous$1;"
                            }
                          ]
                        }
                      },
                      "kinds": [
                        {
                          "distance": 1,
                          "kind": "TestSource",
                          "origins": [
                            {
                              "method": "LSource;.source:()V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_positions": [
                        {"line": 13, "start": 14, "end": 15},
                        {"line": 16, "start": 17, "end": 18}
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Class.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.POSTCONDITION,
                    caller="LClass;.indirect_source:()V",
                    callee="LSource;.source:()V[0: LAnonymous$0;, 1: LAnonymous$1;]",
                    callee_location=SourceLocation(
                        line_no=10,
                        begin_column=12,
                        end_column=13,
                    ),
                    filename="Class.java",
                    titos=[
                        SourceLocation(line_no=13, begin_column=15, end_column=16),
                        SourceLocation(line_no=16, begin_column=18, end_column=19),
                    ],
                    leaves=[("TestSource", 1)],
                    caller_port="result",
                    callee_port="source",
                    type_interval=None,
                    features=[],
                    annotations=[],
                )
            ],
        )

        # Node case.
        self.assertParsed(
            """
            {
              "method": "LClass;.indirect_source:()V",
              "generations": [
                {
                  "port": "Return",
                  "taint": [
                    {
                      "call": {
                        "resolves_to": "LSource;.source:()LData;",
                        "port": "Return",
                        "position": {
                          "path": "Class.java",
                          "line": 10,
                          "start": 11,
                          "end": 12
                        }
                      },
                      "kinds": [
                        {
                          "distance": 1,
                          "kind": "TestSource",
                          "origins": [
                            {
                              "method": "LSource;.source:()V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_positions": [
                        {"line": 13, "start": 14, "end": 15},
                        {"line": 16, "start": 17, "end": 18}
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Class.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.POSTCONDITION,
                    caller="LClass;.indirect_source:()V",
                    callee="LSource;.source:()LData;",
                    callee_location=SourceLocation(
                        line_no=10,
                        begin_column=12,
                        end_column=13,
                    ),
                    filename="Class.java",
                    titos=[
                        SourceLocation(line_no=13, begin_column=15, end_column=16),
                        SourceLocation(line_no=16, begin_column=18, end_column=19),
                    ],
                    leaves=[("TestSource", 1)],
                    caller_port="result",
                    callee_port="result",
                    type_interval=None,
                    features=[],
                    annotations=[],
                )
            ],
        )

        # Test with a complex port.
        self.assertParsed(
            """
            {
              "method": "LSource;.source:()V",
              "generations": [
                {
                  "port": "Return.x.y",
                  "taint": [
                    {
                      "kinds": [
                        {
                          "kind": "TestSource",
                          "origins": [
                            {
                              "method": "LSource;.source:()V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_features": {
                        "may_features": ["via-source"]
                      }
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Source.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.POSTCONDITION,
                    caller="LSource;.source:()V",
                    callee="leaf",
                    callee_location=SourceLocation(
                        line_no=1,
                        begin_column=1,
                        end_column=1,
                    ),
                    filename="Source.java",
                    titos=[],
                    leaves=[("TestSource", 0)],
                    caller_port="result.x.y",
                    callee_port="source",
                    type_interval=None,
                    features=[ParseTraceFeature("via-source", [])],
                    annotations=[],
                )
            ],
        )

        # Test with a parameter source (contains callee position but not callee/port).
        self.assertParsed(
            """
            {
              "method": "LSource;.source:()V",
              "generations": [
                {
                  "port": "Return",
                  "taint": [
                    {
                      "call": {
                        "position": {
                          "path": "Source.java",
                          "line": 2,
                          "start": 3,
                          "end": 4
                        }
                      },
                      "kinds": [
                        {
                          "kind": "TestSource",
                          "origins": [
                            {
                              "method": "LSource;.source:()V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Source.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.POSTCONDITION,
                    caller="LSource;.source:()V",
                    callee="leaf",
                    callee_location=SourceLocation(
                        line_no=2,
                        begin_column=4,
                        end_column=5,
                    ),
                    filename="Source.java",
                    titos=[],
                    leaves=[("TestSource", 0)],
                    caller_port="result",
                    callee_port="source",
                    type_interval=None,
                    features=[],
                    annotations=[],
                )
            ],
        )

        # Test multiple caller ports, callees and kinds (leaves)
        self.assertParsed(
            """
            {
              "method": "LSource;.source:(I)V",
              "generations": [
                {
                  "port": "Return",
                  "taint": [
                    {
                      "kinds": [
                        {
                          "kind": "TestSource"
                        },
                        {
                          "kind": "TestSource2"
                        }
                      ]
                    },
                    {
                      "call": {
                        "resolves_to": "LSource;.source1:()LData;",
                        "port": "Return",
                        "position": {
                          "path": "Class.java",
                          "line": 10,
                          "start": 11,
                          "end": 12
                        }
                      },
                      "kinds": [
                        {
                          "kind": "TestSource",
                          "distance": 1
                        },
                        {
                          "kind": "TestSource2",
                          "distance": 2
                        }
                      ]
                    }
                  ]
                },
                {
                  "port": "Argument(1)",
                  "taint": [
                    {
                      "call": {
                        "resolves_to": "LSource;.source2:()LData;",
                        "port": "Return",
                        "position": {
                          "path": "Class.java",
                          "line": 10,
                          "start": 11,
                          "end": 12
                        }
                      },
                      "kinds": [
                        {
                          "kind": "TestSource",
                          "distance": 3
                        }
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Source.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.POSTCONDITION,
                    caller="LSource;.source:(I)V",
                    callee="leaf",
                    callee_location=SourceLocation(
                        line_no=1,
                        begin_column=1,
                        end_column=1,
                    ),
                    filename="Source.java",
                    titos=[],
                    leaves=[("TestSource", 0), ("TestSource2", 0)],
                    caller_port="result",
                    callee_port="source",
                    type_interval=None,
                    features=[],
                    annotations=[],
                ),
                ParseConditionTuple(
                    type=ParseType.POSTCONDITION,
                    caller="LSource;.source:(I)V",
                    callee="LSource;.source1:()LData;",
                    callee_location=SourceLocation(
                        line_no=10,
                        begin_column=12,
                        end_column=13,
                    ),
                    filename="Source.java",
                    titos=[],
                    leaves=[("TestSource", 1), ("TestSource2", 2)],
                    caller_port="result",
                    callee_port="result",
                    type_interval=None,
                    features=[],
                    annotations=[],
                ),
                ParseConditionTuple(
                    type=ParseType.POSTCONDITION,
                    caller="LSource;.source:(I)V",
                    callee="LSource;.source2:()LData;",
                    callee_location=SourceLocation(
                        line_no=10,
                        begin_column=12,
                        end_column=13,
                    ),
                    filename="Source.java",
                    titos=[],
                    leaves=[("TestSource", 3)],
                    caller_port="argument(1)",
                    callee_port="result",
                    type_interval=None,
                    features=[],
                    annotations=[],
                ),
            ],
        )

    def testModelPreconditions(self) -> None:
        # Leaf case.
        self.assertParsed(
            """
            {
              "method": "LSink;.sink:(LData;)V",
              "sinks": [
                {
                  "port": "Argument(1)",
                  "taint": [
                    {
                      "kinds": [
                        {
                          "kind": "TestSink",
                          "origins": [
                            {
                              "method": "LSink;.sink:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ],
                          "may_features": ["via-obscure"]
                        }
                      ],
                      "local_features": {"always_features": ["via-taint-in-taint-out"]}
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Sink.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.PRECONDITION,
                    caller="LSink;.sink:(LData;)V",
                    callee="leaf",
                    callee_location=SourceLocation(
                        line_no=1,
                        begin_column=1,
                        end_column=1,
                    ),
                    filename="Sink.java",
                    titos=[],
                    leaves=[("TestSink", 0)],
                    caller_port="argument(1)",
                    callee_port="sink",
                    type_interval=None,
                    features=[ParseTraceFeature("always-via-taint-in-taint-out", [])],
                    annotations=[],
                )
            ],
        )

        # Node case.
        self.assertParsed(
            """
            {
              "method": "LClass;.indirect_sink:(LData;LData;)V",
              "sinks": [
                {
                  "port": "Argument(2)",
                  "taint": [
                    {
                      "call": {
                        "resolves_to": "LSink;.sink:(LData;)V",
                        "port": "Argument(1)",
                        "position": {
                          "path": "Class.java",
                          "line": 10,
                          "start": 11,
                          "end": 12
                        }
                      },
                      "kinds": [
                        {
                          "distance": 1,
                          "kind": "TestSink",
                          "origins": [
                            {
                              "method": "LSink;.sink:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_positions": [
                        {"line": 13, "start": 14, "end": 15},
                        {"line": 16, "start": 17, "end": 18}
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Class.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.PRECONDITION,
                    caller="LClass;.indirect_sink:(LData;LData;)V",
                    callee="LSink;.sink:(LData;)V",
                    callee_location=SourceLocation(
                        line_no=10,
                        begin_column=12,
                        end_column=13,
                    ),
                    filename="Class.java",
                    titos=[
                        SourceLocation(line_no=13, begin_column=15, end_column=16),
                        SourceLocation(line_no=16, begin_column=18, end_column=19),
                    ],
                    leaves=[("TestSink", 1)],
                    caller_port="argument(2)",
                    callee_port="argument(1)",
                    type_interval=None,
                    features=[],
                    annotations=[],
                )
            ],
        )

        # Test with a complex port.
        self.assertParsed(
            """
            {
              "method": "LSink;.sink:(LData;)V",
              "sinks": [
                {
                  "port": "Argument(1).x.y",
                  "taint": [
                    {
                      "kinds": [
                        {
                          "kind": "TestSink",
                          "origins": [
                            {
                              "method": "LSink;.sink:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Sink.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.PRECONDITION,
                    caller="LSink;.sink:(LData;)V",
                    callee="leaf",
                    callee_location=SourceLocation(
                        line_no=1,
                        begin_column=1,
                        end_column=1,
                    ),
                    filename="Sink.java",
                    titos=[],
                    leaves=[("TestSink", 0)],
                    caller_port="argument(1).x.y",
                    callee_port="sink",
                    type_interval=None,
                    features=[],
                    annotations=[],
                )
            ],
        )

        # Test with a return sink (has callee position only).
        self.assertParsed(
            """
            {
              "method": "LSink;.sink:(LData;)V",
              "sinks": [
                {
                  "port": "Argument(2)",
                  "taint": [
                    {
                      "call": {
                        "position": {
                          "path": "Sink.java",
                          "line": 2,
                          "start": 3,
                          "end": 4
                        }
                      },
                      "kinds": [
                        {
                          "kind": "TestSink",
                          "origins": [
                            {
                              "method": "LSink;.sink:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ],
                      "local_features": {
                        "may_features": ["via-sink"]
                      }
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Sink.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.PRECONDITION,
                    caller="LSink;.sink:(LData;)V",
                    callee="leaf",
                    callee_location=SourceLocation(
                        line_no=2,
                        begin_column=4,
                        end_column=5,
                    ),
                    filename="Sink.java",
                    titos=[],
                    leaves=[("TestSink", 0)],
                    caller_port="argument(2)",
                    callee_port="sink",
                    type_interval=None,
                    features=[ParseTraceFeature("via-sink", [])],
                    annotations=[],
                )
            ],
        )

        # Test multiple caller ports, callees and kinds (leaves)
        self.assertParsed(
            """
            {
              "method": "LSink;.sink:(LData;LData;)V",
              "sinks": [
                {
                  "port": "Argument(2)",
                  "taint": [
                    {
                      "kinds": [
                        {
                          "kind": "TestSink"
                        },
                        {
                          "kind": "TestSink2"
                        }
                      ]
                    },
                    {
                      "call": {
                        "resolves_to": "LSink;.sink2:(LData;)V",
                        "port": "Argument(1)",
                        "position": {
                          "path": "Class.java",
                          "line": 10,
                          "start": 11,
                          "end": 12
                        }
                      },
                      "kinds": [
                        {
                          "kind": "TestSink",
                          "distance": 1
                        },
                        {
                          "kind": "TestSink2",
                          "distance": 2
                        }
                      ]
                    }
                  ]
                },
                {
                  "port": "Argument(1)",
                  "taint": [
                    {
                      "call": {
                        "resolves_to": "LSink;.sink3:(LData;)V",
                        "port": "Argument(0)",
                        "position": {
                          "path": "Class.java",
                          "line": 10,
                          "start": 5,
                          "end": 7
                        }
                      },
                      "kinds": [
                        {
                          "kind": "TestSink",
                          "distance": 3
                        }
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Sink.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.PRECONDITION,
                    caller="LSink;.sink:(LData;LData;)V",
                    callee="leaf",
                    callee_location=SourceLocation(
                        line_no=1,
                        begin_column=1,
                        end_column=1,
                    ),
                    filename="Sink.java",
                    titos=[],
                    leaves=[("TestSink", 0), ("TestSink2", 0)],
                    caller_port="argument(2)",
                    callee_port="sink",
                    type_interval=None,
                    features=[],
                    annotations=[],
                ),
                ParseConditionTuple(
                    type=ParseType.PRECONDITION,
                    caller="LSink;.sink:(LData;LData;)V",
                    callee="LSink;.sink2:(LData;)V",
                    callee_location=SourceLocation(
                        line_no=10,
                        begin_column=12,
                        end_column=13,
                    ),
                    filename="Sink.java",
                    titos=[],
                    leaves=[("TestSink", 1), ("TestSink2", 2)],
                    caller_port="argument(2)",
                    callee_port="argument(1)",
                    type_interval=None,
                    features=[],
                    annotations=[],
                ),
                ParseConditionTuple(
                    type=ParseType.PRECONDITION,
                    caller="LSink;.sink:(LData;LData;)V",
                    callee="LSink;.sink3:(LData;)V",
                    callee_location=SourceLocation(
                        line_no=10,
                        begin_column=6,
                        end_column=8,
                    ),
                    filename="Sink.java",
                    titos=[],
                    leaves=[("TestSink", 3)],
                    caller_port="argument(1)",
                    callee_port="argument(0)",
                    type_interval=None,
                    features=[],
                    annotations=[],
                ),
            ],
        )

    def testModelParameterTypeOverrides(self) -> None:
        self.assertParsed(
            """
            {
              "method": {
                "name": "LSink;.sink:(LData;)V",
                "parameter_type_overrides": [
                  {
                    "parameter": 0,
                    "type": "LAnonymous$0;"
                  },
                  {
                    "parameter": 1,
                    "type": "LAnonymous$1;"
                  }
                ]
              },
              "sinks": [
                {
                  "port": "Argument(1)",
                  "taint": [
                    {
                      "kinds": [
                        {
                          "kind": "TestSink",
                          "origins": [
                            {
                              "method": {
                                "name": "LSink;.sink:(LData;)V",
                                "parameter_type_overrides": [
                                  {
                                    "parameter": 0,
                                    "type": "LAnonymous$0;"
                                  },
                                  {
                                    "parameter": 1,
                                    "type": "LAnonymous$1;"
                                  }
                                ]
                              },
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "Sink.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.PRECONDITION,
                    caller="LSink;.sink:(LData;)V[0: LAnonymous$0;, 1: LAnonymous$1;]",
                    callee="leaf",
                    callee_location=SourceLocation(
                        line_no=1,
                        begin_column=1,
                        end_column=1,
                    ),
                    filename="Sink.java",
                    titos=[],
                    leaves=[("TestSink", 0)],
                    caller_port="argument(1)",
                    callee_port="sink",
                    type_interval=None,
                    features=[],
                    annotations=[],
                )
            ],
        )

    def testModelWithConnectionPointSource(self) -> None:
        self.assertParsed(
            """
            {
              "method": {
                "name": "Lcom/facebook/analytics/structuredlogger/events/TestEvent;.setFieldA:(I)V"
              },
              "generations": [
                {
                  "port": "Return",
                  "taint": [
                    {
                      "call": {
                        "port": "Anchor.Return"
                      },
                      "kinds": [
                        {
                          "kind": "TestSource",
                          "origins": [
                            {
                              "method": "Lcom/facebook/analytics/structuredlogger/events/TestEvent;.setFieldA:(I)V",
                              "port": "Argument(1)"
                            }
                          ],
                          "canonical_names": [ { "instantiated": "TestEvent:field_a" } ]
                        }
                      ]
                    }
                  ]
               }
              ],
              "position": {
                "line": 1,
                "path": "TestEvent.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.POSTCONDITION,
                    caller="Lcom/facebook/analytics/structuredlogger/events/TestEvent;.setFieldA:(I)V",
                    callee="TestEvent:field_a",
                    callee_location=SourceLocation(
                        line_no=1,
                        begin_column=1,
                        end_column=1,
                    ),
                    filename="TestEvent.java",
                    titos=[],
                    leaves=[("TestSource", 0)],
                    caller_port="result",
                    callee_port="anchor:result",
                    type_interval=None,
                    features=[],
                    annotations=[],
                )
            ],
        )
        self.assertParsed(
            """
            {
              "method": {
                "name": "Lcom/facebook/analytics/structuredlogger/events/TestEvent;.setFieldA:(I)V"
              },
              "generations": [
                {
                  "port": "Return",
                  "taint": [
                    {
                      "call": {
                        "port": "Producer.1234.Argument(2)"
                      },
                      "kinds": [
                        {
                          "kind": "TestSource",
                          "origins": [
                            {
                              "method": "Lcom/facebook/analytics/structuredlogger/events/TestEvent;.setFieldA:(I)V",
                              "port": "Argument(1)"
                            }
                          ],
                          "canonical_names": [ { "instantiated": "LClass;.method:(I)V" }]
                        }
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "TestEvent.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.POSTCONDITION,
                    caller="Lcom/facebook/analytics/structuredlogger/events/TestEvent;.setFieldA:(I)V",
                    callee="LClass;.method:(I)V",
                    callee_location=SourceLocation(
                        line_no=1,
                        begin_column=1,
                        end_column=1,
                    ),
                    filename="TestEvent.java",
                    titos=[],
                    leaves=[("TestSource", 0)],
                    caller_port="result",
                    callee_port="producer:1234:formal(2)",
                    type_interval=None,
                    features=[],
                    annotations=[],
                )
            ],
        )

    def testModelWithConnectionPointSink(self) -> None:
        self.assertParsed(
            """
            {
              "method": {
                "name": "Lcom/facebook/graphql/calls/SomeMutation;.setSomeField:(LData;)V"
              },
              "sinks": [
                {
                  "port": "Argument(1)",
                  "taint": [
                    {
                      "call": {
                        "port": "Anchor.Argument(0)"
                      },
                      "kinds": [
                        {
                          "kind": "TestSink",
                          "canonical_names": [ { "instantiated": "SomeMutation:some_field" } ]
                        }
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "SomeMutation.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.PRECONDITION,
                    caller="Lcom/facebook/graphql/calls/SomeMutation;.setSomeField:(LData;)V",
                    callee="SomeMutation:some_field",
                    callee_location=SourceLocation(
                        line_no=1,
                        begin_column=1,
                        end_column=1,
                    ),
                    filename="SomeMutation.java",
                    titos=[],
                    leaves=[("TestSink", 0)],
                    caller_port="argument(1)",
                    callee_port="anchor:formal(0)",
                    type_interval=None,
                    features=[],
                    annotations=[],
                )
            ],
        )
        self.assertParsed(
            """
            {
              "method": {
                "name": "Lcom/facebook/graphql/calls/SomeMutation;.setSomeField:(LData;)V"
              },
              "sinks": [
                {
                  "port": "Argument(1)",
                  "taint": [
                    {
                      "call": {
                        "port": "Anchor.Argument(-1)"
                      },
                      "kinds": [
                        {
                          "kind": "TestSink",
                          "canonical_names": [ { "instantiated": "SomeMutation:some_field" } ]
                        }
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "SomeMutation.java"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.PRECONDITION,
                    caller="Lcom/facebook/graphql/calls/SomeMutation;.setSomeField:(LData;)V",
                    callee="SomeMutation:some_field",
                    callee_location=SourceLocation(
                        line_no=1,
                        begin_column=1,
                        end_column=1,
                    ),
                    filename="SomeMutation.java",
                    titos=[],
                    leaves=[("TestSink", 0)],
                    caller_port="argument(1)",
                    callee_port="anchor:formal(-1)",
                    type_interval=None,
                    features=[],
                    annotations=[],
                )
            ],
        )

    def testNormalizedPath(self) -> None:
        self.assertParsed(
            """
            {
              "method": "LClass;.indirect_sink:(LData;LData;)V",
              "sinks": [
                {
                  "port": "Argument(2)",
                  "taint": [
                    {
                      "call": {
                        "resolves_to": "Lcom/facebook/Sink$4;.sink:(LData;)V",
                        "port": "Argument(1)",
                        "position": {
                          "path": "unknown",
                          "line": 2,
                          "start": 3,
                          "end": 4
                        }
                      },
                      "kinds": [
                        {
                          "distance": 1,
                          "kind": "TestSink",
                          "origins": [
                            {
                              "method": "Lcom/facebook/Sink$4;.sink:(LData;)V",
                              "port": "Argument(1)"
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }
              ],
              "position": {
                "line": 1,
                "path": "unknown"
              }
            }
            """,
            [
                ParseConditionTuple(
                    type=ParseType.PRECONDITION,
                    caller="LClass;.indirect_sink:(LData;LData;)V",
                    callee="Lcom/facebook/Sink$4;.sink:(LData;)V",
                    callee_location=SourceLocation(
                        line_no=2,
                        begin_column=4,
                        end_column=5,
                    ),
                    filename="Class",
                    titos=[],
                    leaves=[("TestSink", 1)],
                    caller_port="argument(2)",
                    callee_port="argument(1)",
                    type_interval=None,
                    features=[],
                    annotations=[],
                )
            ],
        )
