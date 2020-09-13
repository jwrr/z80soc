//-----------------------------------------------------------------------------
// Block: ctc
// Description:
// This block implements N Counter/Timer Channels for Z80.
//
//
//------------------------------------------------------------------------------


module ctc #(
  parameter N_CH = 4,
  parameter N_CS = 2,
  parameter AWID = 4,
  parameter DWID = 8
)
(
  input                 clk,
  input                 reset_n,
  input                 ce_n,
  input                 m1_n,
  input                 rd_n,
  input                 iorq_n,
  input      [AWID-1:0] a,
  input      [DWID-1:0] din,
  output     [DWID-1:0] dout,
  input                 iei,
  output                ieo,
  output                int_n,
  
  input      [N_CH-1:0] clk_trig,
  input      [N_CH-1:0] zc_to
);  

  reg        [DWID-1:0] dout;
  reg                   ieo;
  reg                   int_n;
  
  
  always @(posedge clk or negedge reset_n) begin
    if (~reset_n) begin
      dout   <= 'h0;
      ieo    <= 1'b0;
      int_n  <= 1'b0;
    end else begin
      dout <= 'h0;
    end
  end
endmodule





