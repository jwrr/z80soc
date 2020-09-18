//-----------------------------------------------------------------------------
// Block: ctc_core
// Description:
// This block implements 1 Counter/Timer Channel for Z80.
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

module ctc_core #(
  parameter DWID = 8
)
(
  input                 clk,
  input                 reset_n,
  input                 ce_n,
  input                 m1_n,
  input                 rd_n,
  input                 iorq_n,
  input      [DWID-1:0] din,
  output     [DWID-1:0] dout,
  output                oe_n,
  input                 iei,
  output                ieo,
  output                int_n,

  input                 clk_trig,
  output                zc_to
);

  reg        [DWID-1:0] dout;
  reg                   oe_n;
  reg                   ieo;
  reg                   int_n;

  reg        [DWID-1:0] ctrl_reg;
  wire                  ctrl1_sw_rst      =  ctrl_reg[1];
  wire                  ctrl3_auto_trig   = ~ctrl_reg[3];
  wire                  ctrl3_ext_trig    =  ctrl_reg[3];
  wire                  ctrl4_trig_fe     = ~ctrl_reg[4];
  wire                  ctrl4_trig_re     =  ctrl_reg[4];
  wire                  ctrl5_prescale16  = ~ctrl_reg[5]; // timer mode only
  wire                  ctrl5_prescale256 =  ctrl_reg[5]; // timer mode only
  wire                  ctrl6_tim_mode    = ~ctrl_reg[6];
  wire                  ctrl6_cnt_mode    =  ctrl_reg[6];
  wire                  ctrl7_int_en      =  ctrl_reg[7];
  
  wire            [7:0] prescale_val      = ctrl5_prescale16 ? 8'h0F : 8'hFF;

  reg        [DWID-1:0] tc_reg;
  reg        [DWID-1:0] cnt;
  reg             [7:0] cnt_prescale;
  reg        [DWID-1:0] vec_reg;
  reg                   clk_trig2;
  reg                   clk_trig_re;
  reg                   clk_trig_fe;

  wire                  we1 = rd_n & ~iorq_n & ~ce_n & m1_n;
  reg                   we2;
  wire                  wstb = we1 & ~we2;
  reg                   tc_next;
  wire                  tc_wstb   = wstb & tc_next;
  wire                  ctrl_wstb = wstb & din[0] & ~tc_next;
  wire                  vec_wstb  = wstb & ~din[0] & ~tc_next;
  reg                   tim_tc_start;


  wire                  rd1 = ~rd_n & ~iorq_n & ~ce_n & m1_n;
  reg                   rd2;

  reg                   ctrl4_trig_re2;
  wire                  sw_trig = ctrl4_trig_re != ctrl4_trig_re2;

  wire                  trig_ld_en = ~ctrl_reg[3];
  wire                  trig_re_en =  ctrl_reg[3] &  ctrl_reg[4];
  wire                  trig_fe_en =  ctrl_reg[3] & ~ctrl_reg[4];
  reg                   trig;
  reg                   triggered;
  reg                   zc_to;

  always @(posedge clk or negedge reset_n) begin
    if (~reset_n) begin
      we2            <= 1'b0;
      rd2            <= 1'b0;
      dout           <= 'h0;
      ctrl_reg       <= 'h0;
      tc_reg         <= 'h0;
      oe_n           <= 1'b1;
      ieo            <= 1'b0;
      int_n          <= 1'b0;
      tc_next        <= 1'b0;
      clk_trig2      <= 1'b0;
      clk_trig_re    <= 1'b0;
      clk_trig_fe    <= 1'b0;
      tim_tc_start   <= 1'b0;
      trig           <= 1'b0;
      cnt            <= 'h0;
      cnt_prescale   <= 8'h0;
      triggered      <= 1'b0;
      ctrl4_trig_re2 <= 1'b0;
      zc_to          <= 1'b0;
    end else begin
      we2    <= we1; // used for edge detect
      rd2    <= rd1; // used for edge detect

      if (rd1 && ~rd2) begin  // capture on rising edge of read
        dout <= cnt;
        oe_n <= 1'b0;
      end
      else begin
        dout <= 'h0;
        oe_n <= 1'b1;
      end

      if (ctrl_wstb && din[2]) begin
        tc_next <= 1'b1;
      end
      else if (tc_wstb) begin
        tc_next <= 1'b0;
      end

      if (tc_wstb) begin
        tc_reg <= din - 1;
      end

      if (ctrl_wstb) begin
        ctrl_reg <= din;
      end

      if (vec_wstb) begin
        vec_reg <= din;
      end

      tim_tc_start <= tc_wstb && ~ctrl3_auto_trig && ~ctrl6_cnt_mode;

      ctrl4_trig_re2 <=  ctrl4_trig_re;
      clk_trig2      <=  clk_trig;
      clk_trig_re    <=  clk_trig && ~clk_trig2 && trig_re_en;
      clk_trig_fe    <= ~clk_trig &&  clk_trig2 && trig_fe_en;;
      trig <= clk_trig_re  || clk_trig_fe  || tim_tc_start || sw_trig;

      if (ctrl1_sw_rst) begin
        triggered <= 1'b0;
      end
      else if (trig) begin
        triggered <= 1'b1;
      end

      if (ctrl6_tim_mode && triggered) begin
        cnt_prescale <= (cnt_prescale==8'h0) ? prescale_val : cnt_prescale - 1;
        if (cnt_prescale==8'h0) begin
          cnt <= (cnt=='h0) ? tc_reg : cnt - 1; 
        end
      end
      else begin
        cnt_prescale <= 'h0;
        cnt <= 'h0;
      end
      
      zc_to <= triggered && cnt=='h0;
      
    end
  end
endmodule





