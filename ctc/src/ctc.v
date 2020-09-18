//-----------------------------------------------------------------------------
// Block: ctc
// Description:
// This block implements N Counter/Timer Channels for Z80.
//
// CHANNEL CONTROL WORD (CCW)
// 0: 0=vector,  1=control
// 1: 0=enabled, 1=sw-reset
// 2: 0=no tc,   1=time constant follows
// 3: 0=start when tc loaded, 1 = start on clk_trig
// 4: 0=clktrig falling edge 1 = rising edge
// 5: 0=prescale 16 1=256
// 6: 0=timer mode  1=counter mode
// 7: 0:disable int 1=enable
// 8-bit time constant follows CCW with bit2=1
//
//------------------------------------------------------------------------------

module ctc #(
  parameter CHAN = 4,
  parameter AWID = 2,
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
  output                oe_n,
  input                 iei,
  output                ieo,
  output                int_n,

  input      [CHAN-1:0] clk_trig,
  output     [CHAN-1:0] zc_to
);

  reg        [DWID-1:0] dout;
  reg                   oe_n;
  reg                   ieo;
  reg                   int_n;

  reg        [DWID-1:0] ctrl_reg[0:CHAN-1];
  reg        [DWID-1:0] tc_reg[0:CHAN-1];
  reg        [DWID-1:0] cnt[0:CHAN-1];
  reg        [DWID-1:0] vec_reg;
  reg        [CHAN-1:0] clk_trig2;
  reg        [CHAN-1:0] trig_re_en; -- trig on rising edge
  reg        [CHAN-1:0] trig_fe_en; -- trig on falling edge
  reg        [CHAN-1:0] trig_ld_en; -- trig on load
  reg        [CHAN-1:0] clk_trig_re;
  reg        [CHAN-1:0] clk_trig_fe;
  
      clk_trig_re <= 'h0;
      clk_trig_fe <= 'h0;
      trig        <= 'h0;

  wire                  we1 = rd_n & ~iorq_n & ~ce_n & m1_n;
  reg                   we2;
  wire                  wstb = we1 & ~we2;
  reg                   tc_next;
  wire                  tc_wstb   = wstb & tc_next;
  wire                  ctrl_wstb = wstb & din[0] & ~tc_next;
  wire                  vec_wstb  = wstb & ~din[0] & (a==0) & ~tc_next;

  wire                  rd1 = ~rd_n & ~iorq_n & ~ce_n & m1_n;
  reg                   rd2;
  int                   ii;

  always @(posedge clk or negedge reset_n) begin
    if (~reset_n) begin
      we2       <= 1'b0;
      rd2       <= 1'b0;
      dout      <= 'h0;
      oe_n      <= 1'b1;
      ieo       <= 1'b0;
      int_n     <= 1'b0;
      tc_next   <= 1'b0;
      clk_trig2 <= 'h0;
      clk_trig_re <= 'h0;
      clk_trig_fe <= 'h0;
      trig        <= 'h0;
    end else begin
      we2    <= we1;
      rd2    <= rd1;
      clk_trig2 <= clk_trig;

      clk_trig_re <= clk_trig & ~clk_trig2;
      clk_trig_fe <= ~clk_trig & clk_trig2;
      
      trig <= clk_trig_re & trig_re_en |
              clk_trig_fe & trig_fe_en |
              load_to     & trig_ld_en |
              sw_trig;

      if (rd1 & ~rd2) begin
        dout <= cnt[a];
        oe_n <= 1'b0;
      end
      else begin
        dout <= 'h0;
        oe_n <= 1'b1;
      end

      if (ctrl_wstb & din[2]) begin
        tc_next <= 1'b1;
      end
      else if (tc_wstb) begin
        tc_next <= 1'b0;
      end

      if (tc_wstb) begin
        tc_reg[a] <= din;
      end

      if (ctrl_wstb) begin
        ctrl_reg[a] <= din;
        trig_ld_en[a] = ~din[3];
        trig_re_en[a] = din[3] & din[4];
        trig_fe_en[a] = din[3] & ~din[4];
      end

      if (vec_wstb) begin
        vec_reg <= din;
      end

      for (ii=0; ii<CHAN; ii=i+1) begin
        if ctrl_reg[ii][6] begin -- counter mode
          if  
      end


    end
  end
endmodule





