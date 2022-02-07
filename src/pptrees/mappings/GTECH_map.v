// Inverter
module inverter
(
    Y, A
);
    output Y;
    input A;

    assign Y = ~A;

endmodule : inverter

// Buffer
module buffer
(
    Y, A
);
    output Y;
    input A;

    GTECH_BUF buffer(.A(A), .Z(Y));

endmodule: buffer

// NAND2
module nand2
(
    Y, A, B
);
    output Y;
    input A, B;

    GTECH_NAND2 nand2(.A(A), .B(B), .Z(Y));

endmodule: nand2

// NOR2
module nor2
(
    Y, A, B
);
    output Y;
    input A, B;

    GTECH_NOR2 nor2(.A(A), .B(B), .Z(Y));

endmodule: nor2

// AND2
module and2
(
    Y, A, B
);
    output Y;
    input A, B;

    GTECH_AND2 and2(.A(A), .B(B), .Z(Y));

endmodule: and2

// OR2
module or2
(
    Y, A, B
);
    output Y;
    input A, B;

    GTECH_OR2 or2(.A(A), .B(B), .Z(Y));

endmodule: or2

// NAND3
module nand3
(
    Y, A, B, C
);
    output Y;
    input A, B, C;

    GTECH_NAND3 nand3(.A(A), .B(B), .C(C), .Z(Y));

endmodule: nand3

// NOR3
module nor3
(
    Y, A, B, C
);
    output Y;
    input A, B, C;

    GTECH_NOR3 nor3(.A(A), .B(B), .C(C), .Z(Y));

endmodule: nor3

// AND3
module and3
(
    Y, A, B, C
);
    output Y;
    input A, B, C;

    GTECH_AND3 and3(.A(A), .B(B), .C(C), .Z(Y));

endmodule: and3

// OR3
module or3
(
    Y, A, B, C
);
    output Y;
    input A, B, C;

    GTECH_OR3 or3(.A(A), .B(B), .C(C), .Z(Y));

endmodule: or3

// NAND4
module nand4
(
    Y, A, B, C, D
);
    output Y;
    input A, B, C, D;

    GTECH_NAND4 nand4(.A(A), .B(B), .C(C), .D(D), .Z(Y));

endmodule: nand4

// NOR4
module nor4
(
    Y, A, B, C, D
);
    output Y;
    input A, B, C, D;

    GTECH_NOR4 nor4(.A(A), .B(B), .C(C), .D(D), .Z(Y));

endmodule: nor4

// AND4
module and4
(
    Y, A, B, C, D
);
    output Y;
    input A, B, C, D;

    GTECH_AND4 and4(.A(A), .B(B), .C(C), .D(D), .Z(Y));

endmodule: and4

// OR4
module or4
(
    Y, A, B, C, D
);
    output Y;
    input A, B, C, D;

    GTECH_OR4 or4(.A(A), .B(B), .C(C), .D(D), .Z(Y));

endmodule: or4

// NAND2B
module nand2b
(
    Y, A, B
);
    output Y;
    input A, B;

    GTECH_AND_NOT nand2b(.A(B), .B(A), .Z(Y));

endmodule: nand2b

// NOR2B
module nor2b
(
    Y, A, B
);
    output Y;
    input A, B;

    GTECH_OR_NOT nor2b(.A(B), .B(A), .Z(Y));

endmodule: nor2b

// AO21
module ao21
(
    Y, A0, A1, B0
);
    output Y;
    input A0, A1, B0;

    GTECH_AO21 ao21(.A(A0), .B(A1), .C(B0), .Z(Y));

endmodule: ao21

// OA21
module oa21
(
    Y, A0, A1, B0
);
    output Y;
    input A0, A1, B0;

    GTECH_OA21 oa21(.A(A0), .B(A1), .C(B0), .Z(Y));

endmodule: oa21

// AOI21
module aoi21
(
    Y, A0, A1, B0
);
    output Y;
    input A0, A1, B0;

    GTECH_AOI21 aoi21(.A(A0), .B(A1), .C(B0), .Z(Y));

endmodule: aoi21

// OAI21
module oai21
(
    Y, A0, A1, B0
);
    output Y;
    input A0, A1, B0;

    GTECH_OAI21 oai21(.A(A0), .B(A1), .C(B0), .Z(Y));

endmodule: oai21

// AO22
module ao22
(
    Y, A0, A1, B0, B1
);
    output Y;
    input A0, A1, B0, B1;

    GTECH_AO22 ao22(.A(A0), .B(A1), .C(B0), .D(B1), .Z(Y));

endmodule: ao22

// OA22
module oa22
(
    Y, A0, A1, B0, B1
);
    output Y;
    input A0, A1, B0, B1;

    GTECH_OA22 oa22(.A(A0), .B(A1), .C(B0), .D(B1), .Z(Y));

endmodule: oa22

// AOI22
module aoi22
(
    Y, A0, A1, B0, B1
);
    output Y;
    input A0, A1, B0, B1;

    GTECH_AOI22 aoi22(.A(A0), .B(A1), .C(B0), .D(B1), .Z(Y));

endmodule: aoi22

// OAI22
module oai22
(
    Y, A0, A1, B0, B1
);
    output Y;
    input A0, A1, B0, B1;

    GTECH_OAI22 oai22(.A(A0), .B(A1), .C(B0), .D(B1), .Z(Y));

endmodule: oai22

// XOR2
module xor2
(
    Y, A, B
);
    output Y;
    input A, B;

    GTECH_XOR2 xor2(.A(A), .B(B), .Z(Y));

endmodule: xor2

// XNOR2
module xnor2
(
    Y, A, B
);
    output Y;
    input A, B;

    GTECH_XNOR2 xnor2(.A(A), .B(B), .Z(Y));

endmodule: xnor2

// MUX2
module mux2
(
    Y, S, A, B
);
    output Y;
    input S, A, B;

    GTECH_MUX2 mux2(.A(A), .B(B), .S(S), .Z(Y));

endmodule: mux2

// MUX2I
module muxi2
(
    Y, S, A, B
);
    output Y;
    input S, A, B;

    GTECH_MUXI2 muxi2(.A(A), .B(B), .S(S), .Z(Y));

endmodule: muxi2
